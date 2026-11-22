package io.max4j.springboot;

import io.max4j.core.MaxClient;
import io.max4j.core.api.BotsApi;
import io.max4j.core.api.ChatsApi;
import io.max4j.core.api.CommentsApi;
import io.max4j.core.api.MessagesApi;
import io.max4j.core.api.SubscriptionsApi;
import io.max4j.core.api.UploadApi;
import io.max4j.core.client.generated.ApiClient;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Lazy;
import org.springframework.util.StringUtils;

@AutoConfiguration
@EnableConfigurationProperties(Max4jProperties.class)
@ConditionalOnProperty(prefix = "max4j", name = "enabled", havingValue = "true")
public class Max4jAutoConfiguration {

  @Bean
  @ConditionalOnMissingBean
  MaxClient maxClient(Max4jProperties properties) {
    if (!StringUtils.hasText(properties.getToken())) {
      throw new IllegalStateException("Property 'max4j.token' is required when max4j is enabled");
    }
    return MaxClient.builder(properties.getToken())
        .baseUrl(properties.getBaseUrl().toString())
        .connectTimeout(properties.getConnectTimeout())
        .readTimeout(properties.getReadTimeout())
        .build();
  }

  @Bean
  @ConditionalOnMissingBean
  ApiClient maxApiClient(MaxClient client) {
    return client.apiClient();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  BotsApi maxBotsApi(MaxClient client) {
    return client.bots();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  ChatsApi maxChatsApi(MaxClient client) {
    return client.chats();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  CommentsApi maxCommentsApi(MaxClient client) {
    return client.comments();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  MessagesApi maxMessagesApi(MaxClient client) {
    return client.messages();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  SubscriptionsApi maxSubscriptionsApi(MaxClient client) {
    return client.subscriptions();
  }

  @Bean
  @Lazy
  @ConditionalOnMissingBean
  UploadApi maxUploadApi(MaxClient client) {
    return client.uploads();
  }
}
