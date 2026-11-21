/* WP00 Drive QC: CSV strings stay in memory; only derived profiles are persisted.
   CommonJS exports also run via functions.exec using the same source.
   No network requests or filesystem writes in this module. */
function parseCSV(text) {
  text = text.replace(/^\uFEFF/, "");
  const records=[]; let row=[], field="", quoted=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(quoted) {
      if(c==='"' && text[i+1]==='"'){field+='"';i++;}
      else if(c==='"') quoted=false;
      else field+=c;
    } else if(c==='"' && !field) quoted=true;
    else if(c===','){row.push(field);field="";}
    else if(c==='\n' || c==='\r'){
      if(c==='\r' && text[i+1]==='\n')i++;
      row.push(field);records.push(row);row=[];field="";
    } else field+=c;
  }
  if(quoted)throw Error("Unclosed CSV quote");
  if(field.length || row.length){row.push(field);records.push(row);}
  const headers=records.shift();
  if(new Set(headers).size!==headers.length)throw Error("Duplicate header");
  const malformed=records.map((r,i)=>r.length===headers.length?null:i+1).filter(x=>x!==null);
  if(malformed.length)throw Error("Malformed rows: "+malformed.slice(0,10));
  return {headers,rows:records.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]])))};
}
function utf8Length(t) {let n=0;for(const c of t){const p=c.codePointAt(0);n+=p<128?1:p<2048?2:p<65536?3:4;}return n;}
function count(values){return Object.fromEntries([...values.reduce((m,v)=>m.set(v,(m.get(v)||0)+1),new Map())]);}
function unique(rows,cols){return new Set(rows.map(r=>JSON.stringify(cols.map(c=>r[c]))));}
function dtype(values){const x=values.filter(v=>v.trim());return !x.length?"unknown":x.every(v=>/^[+-]?\d+$/.test(v))?"integer-like":x.every(v=>Number.isFinite(Number(v)))?"numeric-like":"string";}
function profile(name,text,metadata){
  const table=parseCSV(text), {headers,rows}=table, sample=rows.slice(0,1000);
  const columns=headers.map(h=>{
    const values=rows.map(r=>r[h]), missing=values.filter(v=>!v.trim()).length;
    return {name:h,dtype_observed:dtype(values),missing_count:missing,missing_pct:100*missing/rows.length,
      missing_first_1000:sample.filter(r=>!r[h].trim()).length,sample_size:sample.length,
      distinct_count:new Set(values).size,examples:[...new Set(values)].slice(0,3).map(v=>v.length>180?v.slice(0,180)+" [truncated for display]":v)};
  });
  return {table,profile:{name,source_url:metadata.url,file_id:metadata.id,modified_time:metadata.modified_time,
    size_bytes:Number(metadata.size),fetched_utf8_bytes:utf8Length(text),size_matches:utf8Length(text)===Number(metadata.size),
    scope:"whole_csv_via_connector_in_memory",rows:rows.length,column_count:headers.length,columns,
    duplicate_full_rows_excess:rows.length-unique(rows,headers).size,
    examples:rows.slice(0,3).map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v.length>180?v.slice(0,180)+" [truncated for display]":v])))}};
}
function audit(tables){
  const feat=tables["ilac_feature_v5_atc.csv"].rows, adr=tables["ilac_yan_etki_v5.csv"].rows,
    edges=tables["ilac_protein_eslesmesi_v6.csv"].rows, seq=tables["protein_dizileri_v6.csv"].rows,
    prot=tables["protein_feature_v6.csv"].rows, candidates=tables["sadece_antibiyotikler.csv"].rows,
    links=tables["drug links.csv"].rows;
  const ids=(rs,k)=>new Set(rs.map(r=>r[k]));
  const f=ids(feat,"DrugBank_ID"), a=ids(adr,"DrugBank_ID"), e=ids(edges,"DrugBank_ID");
  const intersection=[...a].filter(x=>e.has(x));
  const subset=adr.filter(r=>intersection.includes(r.DrugBank_ID));
  const atc=tables["ilac_feature_v5_atc.csv"].headers.filter(h=>h.startsWith("ATC_"));
  const drugInfo=rs=>rs.map(r=>({id:r.DrugBank_ID,name:r.Drug_Name}));
  const linkByDb=new Map(links.map(r=>[r["DrugBank ID"],r]));
  const allCid=links.filter(r=>r["PubChem Compound ID"].trim());
  const cidGroups=new Map();
  for(const r of allCid){const k=r["PubChem Compound ID"];if(!cidGroups.has(k))cidGroups.set(k,[]);cidGroups.get(k).push(r["DrugBank ID"]);}
  const collisions=[...cidGroups].filter(([k,v])=>new Set(v).size>1);
  const normalizedChecks={};
  for(const col of ["MW","LogP","HBD","HBA","TPSA"]){
    const v=feat.map(r=>Number(r[col])),mn=Math.min(...v),mx=Math.max(...v);
    normalizedChecks[col]={min:mn,max:mx,rows_matching_global_minmax:feat.filter(r=>Math.abs(Number(r[col+"_norm"])-(Number(r[col])-mn)/(mx-mn))<1e-10).length};
  }
  return {
    drug_counts:{chemistry:f.size,adr:a.size,targets:e.size,adr_target_intersection:intersection.length,three_way:intersection.filter(x=>f.has(x)).length},
    adr:{rows:adr.length,categories:ids(adr,"se_kategori").size,unique_pairs:unique(adr,["DrugBank_ID","se_kategori"]).size,
      intersection_rows:subset.length,intersection_categories:ids(subset,"se_kategori").size,
      intersection_unique_pairs:unique(subset,["DrugBank_ID","se_kategori"]).size,
      possible_pairs:intersection.length*ids(subset,"se_kategori").size,
      unknown_pairs:intersection.length*ids(subset,"se_kategori").size-unique(subset,["DrugBank_ID","se_kategori"]).size,
      duplicate_pair_examples:Object.entries(count(subset.map(r=>JSON.stringify([r.DrugBank_ID,r.se_kategori])))).filter(([k,v])=>v>1).slice(0,5)},
    atc:{column_count:atc.length,all_zero:drugInfo(feat.filter(r=>atc.every(h=>Number(r[h])===0))),
      encoded_J01:feat.filter(r=>atc.filter(h=>h.startsWith("ATC_J01")).some(h=>Number(r[h])===1)).length,
      encoded_nonzero_without_J01:drugInfo(feat.filter(r=>atc.some(h=>Number(r[h])===1)&&!atc.filter(h=>h.startsWith("ATC_J01")).some(h=>Number(r[h])===1)))},
    missing_modalities:{adr_chemistry_without_targets:drugInfo(feat.filter(r=>a.has(r.DrugBank_ID)&&!e.has(r.DrugBank_ID))),
      chemistry_without_adr:drugInfo(feat.filter(r=>!a.has(r.DrugBank_ID))),
      target_without_adr:[...e].filter(x=>!a.has(x)),adr_without_chemistry:[...a].filter(x=>!f.has(x))},
    protein:{sequence_rows:seq.length,feature_rows:prot.length,edge_rows:edges.length,
      unique_drug_protein_pairs:unique(edges,["DrugBank_ID","UniProt_ID"]).size,
      unique_targets:ids(edges,"UniProt_ID").size,organisms:count(seq.map(r=>r.Organizma)),
      header_rows:seq.filter(r=>r.Sequence.startsWith(">")).length,
      collapsed_header_rows:seq.filter(r=>r.Sequence.startsWith(">")&&!r.Sequence.includes("\n")).length,
      raw_standard_AA_only:seq.filter(r=>/^[ACDEFGHIKLMNPQRSTVWY]+$/.test(r.Sequence)).length,
      prefix_score_distribution:count(prot.map(r=>r.kalite_skoru)),
      prefix_rule_matches:prot.filter(r=>Number(r.kalite_skoru)===({P:1,Q:2,O:2}[r.UniProt_ID[0]]||3)).length,
      features_without_sequences:prot.filter(r=>!ids(seq,"UniProt_ID").has(r.UniProt_ID)).map(r=>r.UniProt_ID),
      edges_without_features:[...ids(edges,"UniProt_ID")].filter(x=>!ids(prot,"UniProt_ID").has(x))},
    candidates:{rows:candidates.length,unique_ids:ids(candidates,"DrugBank_ID").size,
      dbsalt:candidates.filter(r=>r.DrugBank_ID.startsWith("DBSALT")).length,
      db:candidates.filter(r=>/^DB\d+$/.test(r.DrugBank_ID)).length,
      atc_values:count(candidates.map(r=>r.ATC_Kodu))},
    bridge:{rows:links.length,unique_db_ids:ids(links,"DrugBank ID").size,
      blank_compound_ids:links.filter(r=>!r["PubChem Compound ID"].trim()).length,
      invalid_nonempty_compound_ids:allCid.filter(r=>!/^\d+$/.test(r["PubChem Compound ID"])).length,
      shared_cid_groups:collisions.length,shared_cid_examples:collisions.slice(0,10),
      feature_db_missing:feat.filter(r=>!linkByDb.has(r.DrugBank_ID)).map(r=>r.DrugBank_ID),
      feature_cid_mismatch:feat.filter(r=>linkByDb.has(r.DrugBank_ID)&&r.pubchem_clean!==linkByDb.get(r.DrugBank_ID)["PubChem Compound ID"]).map(r=>({id:r.DrugBank_ID,feature:r.pubchem_clean,bridge:linkByDb.get(r.DrugBank_ID)["PubChem Compound ID"]})),
      candidate_db_missing:candidates.filter(r=>!linkByDb.has(r.DrugBank_ID)).map(r=>r.DrugBank_ID)},
    normalization_matches_global:normalizedChecks
  };
}
module.exports={parseCSV,utf8Length,profile,audit};

