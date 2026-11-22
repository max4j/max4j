# max4j

[![Build](https://github.com/max4j/max4j/actions/workflows/build.yml/badge.svg)](https://github.com/max4j/max4j/actions/workflows/build.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Java 21 клиент для [MAX Bot API](https://dev.max.ru/docs-api), сгенерированный из официальной
[OpenAPI-схемы](https://github.com/max-messenger/api-schema), и автоконфигурация для Spring Boot 3.

Независимый проект под Apache-2.0. [Участие в разработке](CONTRIBUTING.md) ·
[Сообщить об уязвимости](SECURITY.md).

Maven-координаты: **`io.max4j`**. Версия `0.2.0` подготовлена к публикации в Maven Central
после подтверждения namespace. До публикации её можно собрать локально: `./mvnw install`.

## Модули

- `core` — модели, API-классы и HTTP-клиент без зависимости от Spring;
- `spring-boot-3-starter` — автоконфигурация клиента и опциональный webhook-контроллер.

В репозитории зафиксирована схема MAX Bot API версии `0.0.33`. Java-код API и моделей
генерируется во время сборки с помощью OpenAPI Generator.

## Требования

- Java 21;
- Maven 3.9+ или Maven Wrapper из репозитория;
- токен бота из MAX для реальных запросов.

## Core

```xml
<dependency>
  <groupId>io.max4j</groupId>
  <artifactId>core</artifactId>
  <version>0.2.0</version>
</dependency>
```

```java
import io.max4j.core.MaxClient;
import io.max4j.core.model.BotInfo;

MaxClient max = MaxClient.create(System.getenv("MAX_BOT_TOKEN"));
BotInfo me = max.bots().getMyInfo();
System.out.println(me.getUsername());
```

Через `MaxClient` доступны группы `bots`, `chats`, `comments`, `messages`, `subscriptions`
и `uploads`. Токен передаётся как значение заголовка `Authorization`, как требует MAX API,
без префикса `Bearer`.

## Spring Boot 3 starter

```xml
<dependency>
  <groupId>io.max4j</groupId>
  <artifactId>spring-boot-3-starter</artifactId>
  <version>0.2.0</version>
</dependency>
```

Минимальная конфигурация:

```yaml
max4j:
  enabled: true
  token: ${MAX_BOT_TOKEN}
```

Starter создаёт `MaxClient`, низкоуровневый `ApiClient` и beans всех API-групп. При необходимости
можно переопределить адрес и таймауты:

```yaml
max4j:
  enabled: true
  token: ${MAX_BOT_TOKEN}
  base-url: https://platform-api2.max.ru
  connect-timeout: 10s
  read-timeout: 30s
```

## Webhook

Webhook-контроллер включается только в servlet-приложении, если есть хотя бы один
`MaxUpdateHandler`:

```yaml
max4j:
  enabled: true
  token: ${MAX_BOT_TOKEN}
  webhook:
    enabled: true
    path: /max/webhook
    secret: ${MAX_WEBHOOK_SECRET}
```

```java
import io.max4j.springboot.webhook.MaxUpdateHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class MaxBotConfiguration {

  @Bean
  MaxUpdateHandler maxUpdates() {
    return update -> System.out.println(update.getUpdateType());
  }
}
```

Если `secret` задан, starter сравнивает его с заголовком `X-Max-Bot-Api-Secret` и отклоняет
запросы с неверным значением. После публикации HTTPS endpoint нужно один раз зарегистрировать
подписку в MAX с тем же секретом:

```java
import io.max4j.core.model.SubscriptionRequestBody;
import io.max4j.core.api.SubscriptionsApi;

subscriptionsApi.subscribe(new SubscriptionRequestBody()
    .url("https://example.org/max/webhook")
    .secret(System.getenv("MAX_WEBHOOK_SECRET")));
```

MAX рекомендует webhook для production. Long polling остаётся доступен через
`SubscriptionsApi#getUpdates` для разработки и тестов. Webhook и long polling нельзя
использовать одновременно.

## Обновление схемы

Замените `core/src/main/openapi/max-api.yaml` актуальным файлом из официального репозитория и
запустите `mvnw verify`. Сгенерированные исходники находятся в `core/target` и не коммитятся.

## Сборка и релиз

```bash
./mvnw --batch-mode verify
```

В Windows используйте `mvnw.cmd`. Для релиза обновите версии во всех POM, отправьте тег
`vX.Y.Z` на проверенный коммит `main` и запустите **Actions → Publish Maven package**
с этим тегом и реестром `central`. Подтвердите окружение `release` в **Review deployments**.
Workflow подписывает артефакты, публикует их в Maven Central и ждёт окончания публикации.

В секретах окружения `release` нужны `CENTRAL_USERNAME`, `CENTRAL_PASSWORD`
из [токена Portal](https://central.sonatype.com/usertoken), а также `MAVEN_GPG_KEY`
(экспорт закрытого ключа в ASCII armor) и `MAVEN_GPG_PASSPHRASE`. Открытый ключ должен быть
доступен на keyserver. Локальный `-Pcentral-release deploy` по умолчанию только загружает
пакет для проверки в Portal; публикацию подтверждают отдельно.

## Переход на 0.2.0

Проект развивается в организации [max4j](https://github.com/max4j).
Начиная с 0.2.0, Maven `groupId` всех модулей — `io.max4j`,
Java-пакеты — `io.max4j.core.*` и `io.max4j.springboot.*`.

Обновите `groupId` и версию зависимостей, замените прежний префикс Java-пакетов
на `io.max4j` во всех импортах и настройках сканирования компонентов, затем
пересоберите приложение. `artifactId` модулей и свойства `max4j.*` сохранены.
Это изменение несовместимо на уровне Java-пакетов; не смешивайте модули разных версий.
Ранее опубликованные версии остаются доступными по прежним координатам.

Для публикации требуется подтверждённый namespace `io.max4j` в Sonatype Central
Portal. Владение доменом `max4j.io` подтверждается DNS TXT-записью из Portal.
Само переименование репозитория не меняет Maven-координаты уже выпущенных версий.
