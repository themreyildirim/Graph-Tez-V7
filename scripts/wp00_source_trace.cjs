/* WP00 QC only: trace existing legacy labels back to local SIDER, no label dataset creation. */
const fs = require('node:fs');
const readline = require('node:readline');
async function traceSider(path, queries) {
  const expected = new Set(queries.map(q=>JSON.stringify(q)));
  const matched = new Set();
  const before = fs.statSync(path);
  let rows=0, malformed=0;
  const stream=fs.createReadStream(path, {encoding:'utf8'});
  const lines=readline.createInterface({input:stream,crlfDelay:Infinity});
  for await (const line of lines) {
    if(!line)continue;
    rows++;
    const r=line.split('\t');
    if(r.length!==6){malformed++;continue;}
    if(r[3]!=='PT'||!/^CID0\d+$/.test(r[1]))continue;
    const key=JSON.stringify([String(Number(r[1].slice(4))),r[5],r[4]]);
    if(expected.has(key))matched.add(key);
  }
  const after=fs.statSync(path);
  return {method:'existing legacy (CID, PT name, UMLS) trace only; no cohort or new labels',
    rows_scanned:rows,malformed_rows:malformed,query_rows:queries.length,unique_queries:expected.size,
    matched_unique_queries:matched.size,unmatched_queries:[...expected].filter(k=>!matched.has(k)).map(JSON.parse),
    source_size_bytes:before.size,metadata_unchanged:before.size===after.size&&before.mtimeMs===after.mtimeMs};
}
module.exports={traceSider};
