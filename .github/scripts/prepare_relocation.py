"""Create one-time Central relocation POMs from two trusted release tags."""
from copy import deepcopy
from pathlib import Path
import os
import re
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from validate_release import NS, POMS, git, validate

URI = NS['m']
ET.register_namespace('', URI)
CENTRAL = 'https://repo.maven.apache.org/maven2/'
METADATA = ('name', 'description', 'url', 'licenses', 'developers', 'scm')


def text(pom, path):
    return pom.findtext('/'.join('m:' + part for part in path.split('/')), namespaces=NS)


def add(parent, name, value=None):
    node = ET.SubElement(parent, '{' + URI + '}' + name)
    node.text = value
    return node


def download(url):
    # Only absence (404) is safe to interpret as an unpublished coordinate.
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def pom_url(group, artifact, version):
    return CENTRAL + '/'.join((group.replace('.', '/'), artifact, version,
                              artifact + '-' + version + '.pom'))


def prepare(repo, source_tag, target_tag, output, fetch=download):
    target_sha = validate(repo, target_tag, 'central')
    if not re.fullmatch(r'v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)', source_tag):
        raise ValueError('Source must be a stable release tag')
    if tuple(map(int, source_tag[1:].split('.'))) >= tuple(map(int, target_tag[1:].split('.'))):
        raise ValueError('Source release must precede target release')
    source_sha = git(repo, 'rev-parse', '--verify', f'refs/tags/{source_tag}^{{commit}}')
    ancestry = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor',
                               source_sha, target_sha], capture_output=True)
    if ancestry.returncode:
        raise ValueError('Source release must be an ancestor of target release')
    old = ET.fromstring(git(repo, 'show', f'{source_sha}:pom.xml'))
    target = ET.fromstring(git(repo, 'show', f'{target_sha}:pom.xml'))
    source_group = text(old, 'groupId')
    if not source_group or not re.fullmatch(r'[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+', source_group):
        raise ValueError('Invalid historical namespace')
    if source_group == 'io.max4j' or text(old, 'version') != source_tag[1:]:
        raise ValueError('Source must identify the historical namespace and matching version')
    version = target_tag[1:]
    modules = []
    for path in POMS:
        tagged = ET.fromstring(git(repo, 'show', f'{target_sha}:{path}'))
        artifact = text(tagged, 'artifactId')
        if not artifact or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', artifact):
            raise ValueError('Invalid tagged artifact ID')
        previous = ET.fromstring(git(repo, 'show', f'{source_sha}:{path}'))
        previous_group = text(previous, 'groupId') or text(previous, 'parent/groupId')
        if text(previous, 'artifactId') != artifact or previous_group != source_group:
            raise ValueError('Artifact identity changed beyond namespace relocation')
        published = fetch(pom_url('io.max4j', artifact, version))
        if published is None:
            raise ValueError('Publish all destination artifacts before relocation')
        published = ET.fromstring(published)
        if ((text(published, 'groupId') or text(published, 'parent/groupId')) != 'io.max4j'
                or text(published, 'artifactId') != artifact
                or (text(published, 'version') or text(published, 'parent/version')) != version):
            raise ValueError('Destination POM has unexpected coordinates')
        if fetch(pom_url(source_group, artifact, version)) is not None:
            raise ValueError('Relocation coordinate already exists; never overwrite a release')
        if fetch(pom_url(source_group, artifact, source_tag[1:])) is None:
            raise ValueError('Historical artifact must already exist in Central')
        modules.append((path, artifact))
    if output.exists():
        raise ValueError('Output directory must be new')
    profile = target.find("m:profiles/m:profile[m:id='central-release']", NS)
    if profile is None:
        raise ValueError('Trusted release lacks Central signing configuration')
    parent_artifact = modules[0][1]
    for path, artifact in modules:
        pom = ET.Element('{' + URI + '}project')
        add(pom, 'modelVersion', '4.0.0')
        if path == 'pom.xml':
            add(pom, 'groupId', source_group)
        else:
            parent = add(pom, 'parent')
            add(parent, 'groupId', source_group)
            add(parent, 'artifactId', parent_artifact)
            add(parent, 'version', version)
        add(pom, 'artifactId', artifact)
        if path == 'pom.xml':
            add(pom, 'version', version)
        add(pom, 'packaging', 'pom')
        if path == 'pom.xml':
            for name in METADATA:
                element = target.find('m:' + name, NS)
                if element is None:
                    raise ValueError('Missing destination metadata: ' + name)
                pom.append(deepcopy(element))
            group = add(pom, 'modules')
            for child, _ in modules[1:]:
                add(group, 'module', str(Path(child).parent).replace('\\', '/'))
        else:
            add(pom, 'name', artifact + ' (relocated)')
        relocation = add(add(pom, 'distributionManagement'), 'relocation')
        add(relocation, 'groupId', 'io.max4j')
        add(relocation, 'artifactId', artifact)
        add(relocation, 'version', version)
        add(relocation, 'message', 'Moved to io.max4j. Update Maven coordinates and Java imports; '
            'see https://github.com/max4j/max4j#переход-на-020')
        if path == 'pom.xml':
            add(pom, 'profiles').append(deepcopy(profile))
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(pom, space='  ')
        ET.ElementTree(pom).write(destination, encoding='utf-8', xml_declaration=True)
    return source_group, version


if __name__ == '__main__':
    group, version = prepare(Path.cwd(), os.environ.get('SOURCE_TAG', ''),
                             os.environ.get('TARGET_TAG', ''), Path('target/relocation'))
    print(f'Prepared POM-only relocation from {group}:{version} to io.max4j:{version}')
