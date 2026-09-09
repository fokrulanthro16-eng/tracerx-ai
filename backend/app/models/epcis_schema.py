"""
TraceRx AI - GS1 EPCIS 2.0 Schema (US FDA DSCSA & EU FMD Compliant)
Implements ObjectEvent, AggregationEvent, and JSON-LD serialization for global track-and-trace.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime


class EPCISAction(str, Enum):
    ADD = "ADD"
    OBSERVE = "OBSERVE"
    DELETE = "DELETE"


class BizStep(str, Enum):
    COMMISSIONING = "urn:epcglobal:cbv:bizstep:commissioning"
    SHIPPING = "urn:epcglobal:cbv:bizstep:shipping"
    RECEIVING = "urn:epcglobal:cbv:bizstep:receiving"
    DISPENSING = "urn:epcglobal:cbv:bizstep:dispensing"
    RECALLING = "urn:epcglobal:cbv:bizstep:recalling"


class Disposition(str, Enum):
    ACTIVE = "urn:epcglobal:cbv:disp:active"
    IN_TRANSIT = "urn:epcglobal:cbv:disp:in_transit"
    DISPENSED = "urn:epcglobal:cbv:disp:dispensed"
    RECALLED = "urn:epcglobal:cbv:disp:recalled"
    RETAIL_SOLD = "urn:epcglobal:cbv:disp:retail_sold"


class ReadPoint(BaseModel):
    id: str = Field(..., description="SGLN URI for read point, e.g. urn:epc:id:sgln:0030001.00001.0")


class BizLocation(BaseModel):
    id: str = Field(..., description="SGLN URI for business location")


class QuantityElement(BaseModel):
    epcClass: str = Field(..., description="LGTIN URI e.g. urn:epc:class:lgtin:0030001.012345.LOT123")
    quantity: float = 1.0
    uom: str = "EA"


class ObjectEvent(BaseModel):
    """
    GS1 EPCIS 2.0 ObjectEvent: Represents commissioning, inspection, or dispensation of items.
    """
    type: str = "ObjectEvent"
    eventTime: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    eventTimeZoneOffset: str = "+00:00"
    action: EPCISAction
    bizStep: BizStep
    disposition: Disposition
    epcList: List[str] = Field(default_factory=list, description="List of SGTIN URIs")
    quantityList: Optional[List[QuantityElement]] = None
    readPoint: Optional[ReadPoint] = None
    bizLocation: Optional[BizLocation] = None
    bizTransactionList: Optional[List[Dict[str, str]]] = None

    # TraceRx Cryptographic Merkle extensions
    merkleRoot: Optional[str] = None
    onChainTxHash: Optional[str] = None


class AggregationEvent(BaseModel):
    """
    GS1 EPCIS 2.0 AggregationEvent: Represents physical packaging aggregation into cartons/pallets.
    """
    type: str = "AggregationEvent"
    eventTime: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    eventTimeZoneOffset: str = "+00:00"
    parentID: str = Field(..., description="SSCC or SGTIN of master shipping container/pallet")
    childEPCs: List[str] = Field(..., description="List of unit-level SGTIN blister packs")
    action: EPCISAction = EPCISAction.ADD
    bizStep: BizStep = BizStep.COMMISSIONING
    disposition: Disposition = Disposition.IN_TRANSIT
    readPoint: Optional[ReadPoint] = None
    bizLocation: Optional[BizLocation] = None


class EPCISDocument(BaseModel):
    """
    Complete GS1 EPCIS 2.0 Document in JSON-LD format conforming to GS1 standard.
    """
    context: List[str] = Field(
        default=["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"],
        alias="@context"
    )
    type: str = "EPCISDocument"
    schemaVersion: str = "2.0"
    creationDate: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    epcisBody: Dict[str, Any]

    model_config = {"populate_by_name": True}

    @classmethod
    def create(cls, events: List[BaseModel]) -> "EPCISDocument":
        event_dicts = [e.model_dump(exclude_none=True) for e in events]
        return cls(
            epcisBody={"eventList": event_dicts}
        )
