import time
def lineagejson2text(x):
	textlines = []
	for l in x:
		textlines.append("%(lin)s\t%(family)s\t%(spoligotype)s\t%(rd)s\t%(frac)s" % l)
	return "\n".join(textlines)

def dict_list2text(l,columns = None, mappings = {}):
	headings = list(l[0].keys()) if not columns else columns
	rows = []
	header = "\t".join([mappings[x].title() if x in mappings else x.title() for x in headings])
	for row in l:
		r = "\t".join(["%.3f" % row[x] if type(row[x])==float else str(row[x]).replace("_", " ") for x in headings])
		rows.append(r)
	str_rows = "\n".join(rows)
	return  "%s\n%s\n" % (header,str_rows)

def dict_list2csv(l,columns = None, mappings = {}):
	headings = list(l[0].keys()) if not columns else columns
	rows = []
	header = ",".join([mappings[x].title() if x in mappings else x.title() for x in headings])
	for row in l:
		r = ",".join(["%.3f" % row[x] if type(row[x])==float else "\"%s\"" % str(row[x]).replace("_", " ") for x in headings])
		rows.append(r)
	str_rows = "\n".join(rows)
	return  "%s\n%s\n" % (header,str_rows)



def load_text(text_strings):
	return r"""
TBProfiler report
=================

The following report has been generated by TBProfiler.

Summary
-------
ID: %(id)s
Date: %(date)s
Strain: %(strain)s
Drug-resistance: %(drtype)s

Lineage report
--------------
%(lineage_report)s

Resistance report
-----------------
%(dr_report)s

Other variants report
---------------------
%(other_var_report)s

Analysis pipeline specifications
--------------------------------
Version: %(version)s
%(pipeline)s

Disclaimer
----------
This tool is for Research Use Only and is offered free foruse. The London School
of Hygiene and Tropical Medicine shall have no liability for any loss or damages
of any kind, however sustained relating to the use of this tool.

Citation
--------
Coll, F. et al. Rapid determination of anti-tuberculosis drug resistance from
whole-genome sequences. Genome Medicine 7, 51. 2015
""" % text_strings

def load_csv(text_strings):
	return r"""
TBProfiler report
--------------

Summary
-------
ID,%(id)s
Date,%(date)s
Strain,%(strain)s
Drug-resistance,%(drtype)s

Lineage report
--------------
%(lineage_report)s

Resistance report
-----------------
%(dr_report)s

Other variants report
---------------------
%(other_var_report)s

Analysis pipeline specifications
--------------------------------
Version,%(version)s
%(pipeline)s""" % text_strings


def write_text(json_results,conf,outfile,columns = []):
	drugs = set()
	for l in open(conf["bed"]):
		arr = l.rstrip().split()
		for d in arr[5].split(","):
			drugs.add(d)
	drug_table = []
	results = {}
	annotation = {}
	for x in json_results["dr_variants"]:
		d = x["drug"]
		if d not in results: results[d] = list()
		results[d].append("%s %s (%.2f)" % (x["gene"],x["change"],x["freq"]))
		if d not in annotation: annotation[d] = {key:[] for key in columns}
		for key in columns:
			annotation[d][key].append(x[key])
	for d in drugs:
		if d in results:
			results[d] = ", ".join(results[d]) if len(results[d])>0 else ""
			r = "R" if len(results[d])>0 else ""
			for key in columns:
				annotation[d][key] = ", ".join(annotation[d][key]) if len(annotation[d][key])>0 else ""
		else:
			results[d] = ""
			r = ""
		dictline = {"Drug":d,"Genotypic Resistance":r,"Mutations":results[d]}
		for key in columns:
			dictline[key] = annotation[d][key] if d in annotation else ""
		drug_table.append(dictline)
	pipeline_tbl = [{"Analysis":"Mapping","Program":json_results["pipeline"]["mapper"]},{"Analysis":"Variant Calling","Program":json_results["pipeline"]["variant_caller"]}]
	text_strings = {}
	text_strings["id"] = json_results["id"]
	text_strings["date"] = time.ctime()
	text_strings["strain"] = json_results["sublin"]
	text_strings["drtype"] = json_results["drtype"]
	text_strings["dr_report"] = dict_list2text(drug_table,["Drug","Genotypic Resistance","Mutations"]+columns)
	text_strings["lineage_report"] = dict_list2text(json_results["lineage"],["lin","frac","family","spoligotype","rd"],{"lin":"Lineage","frac":"Estimated fraction"})
	text_strings["other_var_report"] = dict_list2text(json_results["other_variants"],["genome_pos","locus_tag","change","freq"],{"genome_pos":"Genome Position","locus_tag":"Locus Tag","freq":"Estimated fraction"})
	text_strings["pipeline"] = dict_list2text(pipeline_tbl,["Analysis","Program"])
	text_strings["version"] = json_results["tbprofiler_version"]
	o = open(outfile,"w")
	o.write(load_text(text_strings))
	o.close()







def write_csv(json_results,conf,outfile,columns = []):
	drugs = set()
	for l in open(conf["bed"]):
		arr = l.rstrip().split()
		for d in arr[5].split(","):
			drugs.add(d)
	drug_table = []
	results = {}
	annotation = {}
	for x in json_results["dr_variants"]:
		d = x["drug"]
		if d not in results: results[d] = list()
		results[d].append("%s %s (%.2f)" % (x["gene"],x["change"],x["freq"]))
		if d not in annotation: annotation[d] = {key:[] for key in columns}
		for key in columns:
			annotation[d][key].append(x[key])
	for d in drugs:
		if d in results:
			results[d] = ", ".join(results[d]) if len(results[d])>0 else ""
			r = "R" if len(results[d])>0 else ""
			for key in columns:
				annotation[d][key] = ", ".join(annotation[d][key]) if len(annotation[d][key])>0 else ""
		else:
			results[d] = ""
			r = ""
		dictline = {"Drug":d,"Genotypic Resistance":r,"Mutations":results[d]}
		for key in columns:
			dictline[key] = annotation[d][key] if d in annotation else ""
		drug_table.append(dictline)
	pipeline_tbl = [{"Analysis":"Mapping","Program":json_results["pipeline"]["mapper"]},{"Analysis":"Variant Calling","Program":json_results["pipeline"]["variant_caller"]}]
	csv_strings = {}
	csv_strings["id"] = json_results["id"]
	csv_strings["date"] = time.ctime()
	csv_strings["strain"] = json_results["sublin"]
	csv_strings["drtype"] = json_results["drtype"]
	csv_strings["dr_report"] = dict_list2csv(drug_table,["Drug","Genotypic Resistance","Mutations"]+columns)
	csv_strings["lineage_report"] = dict_list2csv(json_results["lineage"],["lin","frac","family","spoligotype","rd"],{"lin":"Lineage","frac":"Estimated fraction"})
	csv_strings["other_var_report"] = dict_list2csv(json_results["other_variants"],["genome_pos","locus_tag","change","freq"],{"genome_pos":"Genome Position","locus_tag":"Locus Tag","freq":"Estimated fraction"})
	csv_strings["pipeline"] = dict_list2csv(pipeline_tbl,["Analysis","Program"])
	csv_strings["version"] = json_results["tbprofiler_version"]
	o = open(outfile,"w")
	o.write(load_csv(csv_strings))
	o.close()
