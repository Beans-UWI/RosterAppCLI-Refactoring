from App.database import db
from .evenDistributionScheduler import EvenDistributionScheduler
from .balanceShiftsScheduler import BalanceShiftsScheduler
from .minimizeDaysScheduler import MinimizeDaysScheduler

class SchedulerFactory:
    STRATEGIES = {
        "evenDistribution": EvenDistributionScheduler,
        "balanceShifts": BalanceShiftsScheduler,
        "minimizeDays": MinimizeDaysScheduler
    }

    # Returns the selected scheduling strategy
    @staticmethod
    def get_scheduler(scheduler_type):
        scheduler_class = SchedulerFactory.STRATEGIES.get(scheduler_type)
        if not scheduler_class:
            raise ValueError(f"Unknown scheduler type '{scheduler_type}'. Available types: {list(SchedulerFactory.STRATEGIES.keys())}")
        return scheduler_class()
