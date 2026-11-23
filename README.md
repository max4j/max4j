# max4j

[![Build](https://github.com/max4j/max4j/actions/workflows/build.yml/badge.svg)](https://github.com/max4j/max4j/actions/workflows/build.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Java 21 клиент для [MAX Bot API](https://dev.max.ru/docs-api), сгенерированный из официальной
[OpenAPI-схемы](https://github.com/max-messenger/api-schema), и автоконфигурация для Spring Boot 3.

Независимый проект под Apache-2.0. [Участие в разработке](CONTRIBUTING.md) ·
[Сообщить об уязвимости](SECURITY.md).

Maven-координаты: **`io.max4j`**. Актуальная версия — **`0.4.2`**.
Сборка из исходников: `./mvnw install`.

## Модули

- `core` — модели, API-классы и HTTP-клиент без зависимости от Spring;
- `spring-boot-3-starter`, `spring-boot-4-starter` — автоконфигурация клиента и опциональный webhook-контроллер.

В репозитории зафиксирована схема MAX Bot API версии `0.0.34`. Java-код API и моделей
генерируется во время сборки с помощью OpenAPI Generator.

## Core

```xml
<dependency>
  <groupId>io.max4j</groupId>
  <artifactId>core</artifactId>
  <version>0.4.2</version>
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
  <version>0.4.2</version>
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