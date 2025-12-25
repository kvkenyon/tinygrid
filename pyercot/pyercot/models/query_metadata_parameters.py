from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.query_metadata_parameters_additional_property import QueryMetadataParametersAdditionalProperty


T = TypeVar("T", bound="QueryMetadataParameters")


@_attrs_define
class QueryMetadataParameters:
    """ """

    additional_properties: dict[str, QueryMetadataParametersAdditionalProperty] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.query_metadata_parameters_additional_property import QueryMetadataParametersAdditionalProperty

        d = dict(src_dict)
        query_metadata_parameters = cls()

        additional_properties = {}
        for prop_name, prop_value in d.items():
            # Handle both dict values and simple values (strings, numbers, etc.)
            if isinstance(prop_value, Mapping):
                additional_property = QueryMetadataParametersAdditionalProperty.from_dict(prop_value)
            else:
                # For simple values (strings, numbers, etc.), create an empty object
                # and store the value directly - the parameters are just key-value pairs
                additional_property = QueryMetadataParametersAdditionalProperty()
                # Store the simple value as a special property
                additional_property.additional_properties = {"value": prop_value}

            additional_properties[prop_name] = additional_property

        query_metadata_parameters.additional_properties = additional_properties
        return query_metadata_parameters

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> QueryMetadataParametersAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: QueryMetadataParametersAdditionalProperty) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
