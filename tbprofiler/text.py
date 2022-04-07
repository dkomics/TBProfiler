import time
from .reformat import get_summary
from pathogenprofiler import errlog, debug, unlist
from .utils import get_drug_list

_DRUGS = [
    'rifampicin', 'isoniazid', 'ethambutol', 'pyrazinamide', 'streptomycin',
    'fluoroquinolones', 'amikacin', 'capreomycin', 'kanamycin',
    'cycloserine',  'ethionamide', 'clofazimine', 'para-aminosalicylic_acid',
    'delamanid', 'bedaquiline', 'linezolid'
]

def lineagejson2text(x):
    textlines = []
    for l in x:
        textlines.append("%(lin)s\t%(family)s\t%(spoligotype)s\t%(rd)s\t%(frac)s" % l)
    return "\n".join(textlines)

def return_fields(obj,args,i=0):
    largs = args.split(".")
    if i+1>len(largs):
        return obj
    sub_obj = obj[largs[i]]
    if isinstance(sub_obj,dict):
        return return_fields(sub_obj,args,i+1)
    elif isinstance(sub_obj,list):
        return [return_fields(x,args,i+1) for x in sub_obj]
    else:
        return sub_obj

def dict_list2text(l,columns = None, mappings = None,sep="\t"):
    headings = list(l[0].keys()) if not columns else columns
    rows = []
    header = sep.join([mappings[x].title() if (mappings!=None and x in mappings) else x.title() for x in headings])
    for row in l:
        r = sep.join([variable2string(return_fields(row,x)) for x in headings])
        rows.append(r)
    str_rows = "\n".join(rows)
    return  "%s\n%s\n" % (header,str_rows)


def variable2string(var,quote=False):
    q = '"' if quote else ""
    if isinstance(var,float):
        return "%.3f" % var
    elif isinstance(var,dict):
        return "%s%s%s" % (q,",".join(list(var)),q)
    elif isinstance(var,list):
        return "%s%s%s" % (q,",".join(var),q)
    else:
        return "%s%s%s" % (q,str(var),q)

def load_spoligotype_report(text_strings):
    return r"""
TBProfiler spoligotype report
=================

Summary
-------
ID%(sep)s%(id)s
Binary-spoligotype%(sep)s%(binary)s
Octal-spologotype%(sep)s%(octal)s

Spacers
-------
%(spacer_report)s
""" % text_strings

def load_text(text_strings):
    txt = r"""
TBProfiler report
=================

The following report has been generated by TBProfiler.

Summary
-------
ID%(sep)s%(id)s
Date%(sep)s%(date)s
Strain%(sep)s%(strain)s
Drug-resistance%(sep)s%(drtype)s
Median Depth%(sep)s%(med_dp)s

Lineage report
--------------
%(lineage_report)s
""" % text_strings

    if "spacers" in text_strings:
        txt += """
Spoligotype report
------------------
Binary%(sep)s%(binary)s
Octal%(sep)s%(octal)s
""" % text_strings

    txt += """
Resistance report
-----------------
%(dr_report)s

Resistance variants report
-----------------
%(dr_var_report)s

Other variants report
---------------------
%(other_var_report)s

Coverage report
---------------------
%(coverage_report)s

Missing positions report
---------------------
%(missing_report)s
""" % text_strings
    if "spacers" in text_strings:
        txt += """Spoligotype spacers
-------------------
%(spacers)s
""" % text_strings

    txt += """
Analysis pipeline specifications
--------------------------------
Pipeline version%(sep)s%(version)s
Database version%(sep)s%(db_version)s
%(pipeline)s

Citation
--------
Coll, F. et al. Rapid determination of anti-tuberculosis drug resistance from
whole-genome sequences. Genome Medicine 7, 51. 2015

Phelan, JE. et al. Integrating informatics tools and portable sequencing 
technology for rapid detection of resistance to anti-tuberculous drugs. 
Genome Medicine 11, 41. 2019
""" % text_strings
    return txt
def write_spoligotype_report(json_results,conf,outfile,sep="\t"):
    json_results["spacer_report"] = dict_list2text(json_results["spacers"],["name","count"],{"name":"Spacer","count":"Count"},sep=sep)
    if sep=="\t":
        json_results["sep"] = ": "
    else:
        json_results["sep"] = ","
    with open(outfile,"w") as O:
        O.write(load_spoligotype_report(json_results))

def write_text(json_results,conf,outfile,columns = None,reporting_af = 0.0,sep="\t"):
    json_results = get_summary(json_results,conf,columns = columns,reporting_af=reporting_af)
    drug_list = get_drug_list(conf["bed"])
    drug_types = {"fluoroquinolones":["ofloxacin","moxifloxacin","levofloxacin","ciprofloxacin"]}
    for dt in drug_types:
        if dt not in drug_list:
            for d in drug_types[dt]:
                if d in drug_list:
                    _DRUGS.append(d)
    json_results["drug_table"] = [[y for y in json_results["drug_table"] if y["Drug"].upper()==d.upper()][0] for d in _DRUGS if d in drug_list]
    for var in json_results["dr_variants"]:
        var["drug"] = "; ".join([d["drug"] for d in var["drugs"]])

    text_strings = {}
    text_strings["id"] = json_results["id"]
    text_strings["date"] = time.ctime()
    text_strings["strain"] = json_results["sublin"]
    text_strings["drtype"] = json_results["drtype"]
    text_strings["med_dp"] = json_results["qc"]["median_coverage"] if json_results['input_data_source'] in ('bam','fastq') else "NA"
    if "spoligotype" in json_results:
        text_strings["binary"] = json_results["spoligotype"]["binary"]
        text_strings["octal"] = json_results["spoligotype"]["octal"]
        text_strings["spacers"] = dict_list2text(json_results["spoligotype"]["spacers"],["name","count"])
    text_strings["dr_report"] = dict_list2text(json_results["drug_table"],["Drug","Genotypic Resistance","Mutations"]+columns if columns else [],sep=sep)
    text_strings["lineage_report"] = dict_list2text(json_results["lineage"],["lin","frac","family","spoligotype","rd"],{"lin":"Lineage","frac":"Estimated fraction"},sep=sep)
    text_strings["dr_var_report"] = dict_list2text(json_results["dr_variants"],["genome_pos","locus_tag","gene","change","freq","drugs.drug"],{"genome_pos":"Genome Position","locus_tag":"Locus Tag","freq":"Estimated fraction","drugs.drug":"Drug"},sep=sep)
    text_strings["other_var_report"] = dict_list2text(json_results["other_variants"],["genome_pos","locus_tag","gene","change","freq"],{"genome_pos":"Genome Position","locus_tag":"Locus Tag","freq":"Estimated fraction"},sep=sep)
    text_strings["coverage_report"] = dict_list2text(json_results["qc"]["gene_coverage"], ["gene","locus_tag","cutoff","fraction"],sep=sep) if "gene_coverage" in json_results["qc"] else "Not available"
    text_strings["missing_report"] = dict_list2text(json_results["qc"]["missing_positions"],["gene","locus_tag","position","variants","drugs"],sep=sep) if "gene_coverage" in json_results["qc"] else "Not available"
    text_strings["pipeline"] = dict_list2text(json_results["pipeline"],["Analysis","Program"],sep=sep)
    text_strings["version"] = json_results["tbprofiler_version"]
    tmp = json_results["db_version"]
    text_strings["db_version"] = "%s_%s_%s_%s" % (tmp["name"],tmp["commit"],tmp["Author"],tmp["Date"])
    if sep=="\t":
        text_strings["sep"] = ": "
    else:
        text_strings["sep"] = ","
    with open(outfile,"w") as O:
        O.write(load_text(text_strings))