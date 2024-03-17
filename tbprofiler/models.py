from pydantic import BaseModel, Field
from typing import Optional, List, Union
from pathogenprofiler import object_list2text
from pathogenprofiler.models import BamQC, FastaQC, VcfQC, Variant, DrVariant
from datetime import datetime



class Lineage(BaseModel):
    """
    A class to hold information about a lineage
    
    Attributes
    ----------
    fraction : float
        Fraction of reads belonging to this lineage
    lineage : str
        Name of the lineage
    family : str
        Family names associated with the lineage
    rd : Optional[str]
        RDs associated with the lineage
    """
    fraction: float
    lineage: str
    family: str
    rd: Optional[str] = None


class Result(BaseModel):
    """
    A class to hold information about a TBProfiler result
    
    Attributes
    ----------
    id : str
        Sample ID
    timestamp : datetime
        Time of analysis
    tbprofiler_version : str
        TBProfiler version
    db_version : dict
        TBProfiler database version
    """
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tbprofiler_version: str
    db_version: dict

class TbDrVariant(DrVariant):
    locus_tag: str
    gene_associated_drugs: List[str] = []

class TbVariant(Variant):
    locus_tag: str
    gene_associated_drugs: List[str] = []

class Spacer(BaseModel):
    name: str
    seq: str
    count: int

class Spoligotype(BaseModel):
    binary: str
    octal: str
    family: str
    SIT: str
    countries: str
    spacers: List[Spacer]

    def __repr__(self) -> str:
        return self.octal

class LinkedSample(BaseModel):
    sample: str
    distance: float
    positions: List[int]

class ProfileResult(Result):
    notes: List[str] = []
    lineage: Optional[List[Lineage]] = []
    main_lineage: str = None
    sub_lineage: str = None
    spoligotype: Optional[Spoligotype] = None
    drtype: str
    dr_variants: List[TbDrVariant] = []
    other_variants: List[TbVariant] = []
    qc_fail_variants: List[Union[TbDrVariant,TbVariant]] = []
    qc: Union[BamQC, FastaQC, VcfQC]
    linked_samples: List[LinkedSample] = []

    def get_qc(self):
        if isinstance(self.qc, (BamQC, FastaQC)):
            text = object_list2text(l = self.qc.target_qc)
        else:
            text = "Not available for VCF input"
        return text

class LineageResult(Result):
    lineage: Optional[List[Lineage]] = []
    main_lineage: str = None
    sub_lineage: str = None

    def get_lineage(self):
        if self.lineage:
            return object_list2text(l = self.lineage)
        else:
            return "Not available"
