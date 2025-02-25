import json
from typing import Dict, Any
from jsonschema import validate, ValidationError, SchemaError, Draft202012Validator
from . import config_manager
from ..utils.exceptions import ConfigurationError

class ConfigValidator:
    """
    Validates configuration files against a JSON schema.
    """

    def __init__(self, schema_path: str):
        """
        Initializes the ConfigValidator with the path to the JSON schema.

        Args:
            schema_path (str): The path to the JSON schema file.
        """
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """
        Loads the JSON schema from the specified path.

        Returns:
            Dict[str, Any]: The loaded JSON schema.

        Raises:
            ConfigurationError: If the schema file is not found or is invalid JSON.
        """
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            Draft202012Validator.check_schema(schema)
            return schema
        except FileNotFoundError:
            raise ConfigurationError(f"Schema file not found: {self.schema_path}")
        except (json.JSONDecodeError, SchemaError) as e:
            raise ConfigurationError(f"Invalid schema file: {str(e)}")

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validates the given configuration against the loaded JSON schema.

        Args:
            config (Dict[str, Any]): The configuration to validate.

        Raises:
            ConfigurationError: If the configuration does not match the schema.
        """
        try:
            validate(instance=config, schema=self.schema)
            self._validate_version(config)
        except ValidationError as e:
            raise ConfigurationError(f"Configuration does not match schema: {str(e)}")

    def _validate_version(self, config: Dict[str, Any]) -> None:
        """
        Validates the configuration version.

        Args:
            config (Dict[str, Any]): The configuration to validate.

        Raises:
            ConfigurationError: If the configuration version is missing or invalid.
        """
        version = config.get("config_version")
        if version is None:
            raise ConfigurationError("Configuration version is missing.")
        if not isinstance(version, int):
            raise ConfigurationError("Configuration version must be an integer.")
        # Add more version validation logic here if needed, e.g., checking against a supported range

    def validate_required_fields(self, config: Dict[str, Any], required_fields: list) -> None:
        """
        Validates that all required fields are present in the configuration.

        Args:
            config (Dict[str, Any]): The configuration to validate.
            required_fields (list): A list of required field names.

        Raises:
            ConfigurationError: If any required fields are missing.
        """
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ConfigurationError(f"Missing required fields: {', '.join(missing_fields)}")

    def validate_data_types(self, config: Dict[str, Any], field_types: Dict[str, type]) -> None:
        """
        Validates the data types of specific fields in the configuration.

        Args:
            config (Dict[str, Any]): The configuration to validate.
            field_types (Dict[str, type]): A dictionary mapping field names to their expected data types.

        Raises:
            ConfigurationError: If any fields have incorrect data types.
        """
        for field, expected_type in field_types.items():
            if field in config and not isinstance(config[field], expected_type):
                raise ConfigurationError(
                    f"Field '{field}' has incorrect data type: expected {expected_type}, got {type(config[field])}"
                )

    def validate_value_ranges(self, config: Dict[str, Any], field_ranges: Dict[str, tuple]) -> None:
        """
        Validates that the values of specific fields are within the allowed ranges.

        Args:
            config (Dict[str, Any]): The configuration to validate.
            field_ranges (Dict[str, tuple]): A dictionary mapping field names to their allowed ranges (min, max).

        Raises:
            ConfigurationError: If any fields have values outside the allowed ranges.
        """
        for field, (min_val, max_val) in field_ranges.items():
            if field in config:
                value = config[field]
                if not min_val <= value <= max_val:
                    raise ConfigurationError(
                        f"Field '{field}' value {value} is outside the allowed range: {min_val} - {max_val}"
                    )

    def validate_format(self, config: Dict[str, Any], field_formats: Dict[str, str]) -> None:
        """
        Validates the format of specific fields in the configuration using regular expressions.

        Args:
            config (Dict[str, Any]): The configuration to validate.
            field_formats (Dict[str, str]): A dictionary mapping field names to their regular expression formats.

        Raises:
            ConfigurationError: If any fields do not match the required format.
        """
        # Placeholder for format validation using regular expressions.
        # Implement regex validation here if needed.
        pass