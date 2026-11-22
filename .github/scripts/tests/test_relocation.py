import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parents[1]))
import prepare_relocation as relocation


class RelocationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=os.name == 'nt')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.output = self.repo / 'generated'
        self.published = {}
        self.git('init', '-b', 'main')
        self.write_release('example.previous', '0.1.1')
        self.git('add', '.')
        self.git('commit', '-m', 'Historical fixture')
        self.git('tag', 'v0.1.1')
        self.write_release('io.max4j', '0.2.0')
        self.git('add', '.')
        self.git('commit', '-m', 'Destination fixture')
        self.git('tag', 'v0.2.0')
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'user.name=Synthetic Test',
            '-c', 'user.email=test@example.invalid', '-C', str(self.repo), *args],
            text=True, stderr=subprocess.PIPE).strip()

    def write_release(self, group, version):
        for path in relocation.POMS:
            artifact = 'max4j-parent' if path == 'pom.xml' else Path(path).parent.name
            if path == 'pom.xml':
                coordinate = f'<groupId>{group}</groupId><artifactId>{artifact}</artifactId><version>{version}</version>'
                metadata = ''.join(f'<{tag}>fixture</{tag}>' for tag in relocation.METADATA)
                metadata += '<profiles><profile><id>central-release</id></profile></profiles>'
            else:
                coordinate = f'<parent><groupId>{group}</groupId><artifactId>max4j-parent</artifactId><version>{version}</version></parent><artifactId>{artifact}</artifactId>'
                metadata = ''
            body = f'<project xmlns="{relocation.URI}">{coordinate}{metadata}</project>'
            destination = self.repo / path
            destination.parent.mkdir(exist_ok=True)
            destination.write_text(body, encoding='utf-8')
            self.published[relocation.pom_url(group, artifact, version)] = body.encode()

    def prepare(self, source='v0.1.1', target='v0.2.0'):
        return relocation.prepare(self.repo, source, target, self.output, self.published.get)

    def test_generates_three_pom_only_redirects_to_published_release(self):
        self.assertEqual(('example.previous', '0.2.0'), self.prepare())
        self.assertEqual(3, len(list(self.output.rglob('*.xml'))))
        for path in relocation.POMS:
            doc = ET.parse(self.output / path).getroot()
            self.assertEqual('pom', relocation.text(doc, 'packaging'))
            self.assertEqual('io.max4j', relocation.text(doc, 'distributionManagement/relocation/groupId'))
            self.assertEqual(relocation.text(doc, 'artifactId'), relocation.text(doc, 'distributionManagement/relocation/artifactId'))
            self.assertEqual('0.2.0', relocation.text(doc, 'distributionManagement/relocation/version'))
            self.assertIsNone(doc.find('m:dependencies', relocation.NS))

    def test_refuses_to_overwrite_any_published_coordinate(self):
        self.published[relocation.pom_url('example.previous', 'core', '0.2.0')] = b'exists'
        with self.assertRaisesRegex(ValueError, 'never overwrite'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_requires_every_destination_to_be_public(self):
        del self.published[relocation.pom_url('io.max4j', 'spring-boot-3-starter', '0.2.0')]
        with self.assertRaisesRegex(ValueError, 'destination artifacts'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_rejects_unexpected_destination_coordinates(self):
        url = relocation.pom_url('io.max4j', 'core', '0.2.0')
        self.published[url] = self.published[url].replace(b'io.max4j', b'example.other')
        with self.assertRaisesRegex(ValueError, 'unexpected coordinates'):
            self.prepare()

    def test_requires_original_artifacts_to_exist(self):
        del self.published[relocation.pom_url('example.previous', 'core', '0.1.1')]
        with self.assertRaisesRegex(ValueError, 'Historical artifact'):
            self.prepare()

    def test_rejects_same_version_and_injected_source_tags(self):
        for tag in ('v0.2.0', '--help', 'v0.1.1; echo injected', 'v0.1.1\n::error::injected'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.prepare(source=tag)

    def test_rejects_source_outside_release_ancestry(self):
        self.git('switch', '--orphan', 'foreign')
        self.write_release('example.previous', '0.1.0')
        self.git('add', '.')
        self.git('commit', '-m', 'Foreign fixture')
        self.git('tag', 'v0.1.0')
        with self.assertRaisesRegex(ValueError, 'ancestor'):
            self.prepare(source='v0.1.0')

    def test_rejects_existing_output_directory(self):
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, 'Output directory'):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
