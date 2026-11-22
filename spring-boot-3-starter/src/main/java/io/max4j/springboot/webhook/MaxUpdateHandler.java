package io.max4j.springboot.webhook;

import io.max4j.core.model.Update;

@FunctionalInterface
public interface MaxUpdateHandler {

  void handle(Update update);
}
