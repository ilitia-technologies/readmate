from readmate.utils.logger import set_logger


class TokenUsageTracker:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TokenUsageTracker, cls).__new__(cls, *args, **kwargs)
            # Place any initialization here
            cls._instance.token_usage = 0
            cls._instance.total_cost = 0
            cls._instance.logger = set_logger()
        return cls._instance

    def log_token_usage(self, tokens_used: int):
        self.token_usage += tokens_used
        self.persist_token_usage()

    def log_cost(self, cost: float):
        self.total_cost += cost
        self.persist_total_cost()

    def get_total_usage(self):
        return self.token_usage

    def get_total_cost(self):
        return self.total_cost

    def persist_token_usage(self):
        # Placeholder for any persistence logic
        self.logger.info(f"Total tokens used so far: {self.token_usage}")

    def persist_total_cost(self):
        # Placeholder for any persistence logic
        self.logger.info(f"Total cost $ so far: {self.total_cost}")
