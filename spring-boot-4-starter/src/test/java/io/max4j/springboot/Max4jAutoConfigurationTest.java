package io.max4j.springboot;

import static org.assertj.core.api.Assertions.assertThat;

import io.max4j.core.MaxClient;
import io.max4j.core.api.BotsApi;
import io.max4j.core.api.ChatsApi;
import io.max4j.core.api.CommentsApi;
import io.max4j.core.api.MessagesApi;
import io.max4j.core.api.SubscriptionsApi;
import io.max4j.core.api.UploadApi;
import io.max4j.core.client.generated.ApiClient;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.AutoConfigurations;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Configuration;

class Max4jAutoConfigurationTest {

  private final ApplicationContextRunner contextRunner = new ApplicationContextRunner()
      .withConfiguration(AutoConfigurations.of(io.max4j.springboot.Max4jAutoConfiguration.class));

  @Test
  void staysDisabledByDefault() {
    contextRunner.run(context -> assertThat(context).doesNotHaveBean(MaxClient.class));
  }

  @Test
  void createsClientAndAllApiGroups() {
    contextRunner
        .withPropertyValues("max4j.enabled=true", "max4j.token=test-token")
        .run(context -> {
          assertThat(context).hasSingleBean(MaxClient.class);
          assertThat(context).hasSingleBean(ApiClient.class);
          assertThat(context).hasSingleBean(BotsApi.class);
          assertThat(context).hasSingleBean(ChatsApi.class);
          assertThat(context).hasSingleBean(CommentsApi.class);
          assertThat(context).hasSingleBean(MessagesApi.class);
          assertThat(context).hasSingleBean(SubscriptionsApi.class);
          assertThat(context).hasSingleBean(UploadApi.class);
        });
  }

  @Test
  void failsFastWhenEnabledWithoutToken() {
    contextRunner
        .withPropertyValues("max4j.enabled=true")
        .run(context -> assertThat(context).hasFailed());
  }

  @Test
  void discoversClientThroughStarterMetadata() {
    new ApplicationContextRunner()
        .withUserConfiguration(AutoConfiguredApplication.class)
        .withPropertyValues("max4j.enabled=true", "max4j.token=test-token")
        .run(context -> {
          assertThat(context).hasNotFailed();
          assertThat(context).hasSingleBean(MaxClient.class);
          assertThat(context).hasSingleBean(BotsApi.class);
        });
  }

  @Configuration(proxyBeanMethods = false)
  @EnableAutoConfiguration
  static class AutoConfiguredApplication {
  }
}
