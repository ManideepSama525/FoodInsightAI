class FoodInsightError(Exception):
    """Base application exception."""

class FileValidationError(FoodInsightError):
    pass

class ResourceNotFoundError(FoodInsightError):
    pass

class DependencyUnavailableError(FoodInsightError):
    pass
