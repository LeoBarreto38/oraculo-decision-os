import { useMemo } from 'react';
import { Background, Controls, MarkerType, MiniMap, ReactFlow, type Edge, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { RefreshCw } from 'lucide-react';
import { DataModeBanner, PageHeader, StatusBadge } from '../components/ui';
import { fallbackGraph } from '../data/fallback';
import { useApiResource } from '../hooks/useApiResource';
import { api } from '../services/api';

const nodeColor:Record<string,string>={Pessoa:'#c8f06a',Meta:'#78b8d8',Projeto:'#a78bfa','Decisão':'#fbbf24','Hipótese':'#fb7185',Evidência:'#94a3b8'};

export default function MapPage(){
  const resource=useApiResource(api.map,fallbackGraph);
  const nodes=useMemo<Node[]>(()=>resource.data.nodes.map((node,index)=>({id:String(node.id),position:node.position||{x:(index%4)*240,y:Math.floor(index/4)*150},data:{label:<div className="min-w-28"><span className="block font-mono text-[9px] uppercase tracking-widest text-slate-500">{node.type||node.reference_type||'Entidade'}</span><span className="mt-1 block text-xs font-semibold text-slate-100">{node.label}</span></div>},style:{background:'#11171b',border:`1px solid ${nodeColor[node.type||'']||'#34414a'}`,borderRadius:10,color:'#fff',padding:12,boxShadow:'0 10px 30px rgba(0,0,0,.28)'}})),[resource.data.nodes]);
  const edges=useMemo<Edge[]>(()=>resource.data.edges.map((edge,index)=>({id:String(edge.id||`${edge.source}-${edge.target}-${index}`),source:String(edge.source),target:String(edge.target),label:edge.relation,markerEnd:{type:MarkerType.ArrowClosed,color:'#65727b'},style:{stroke:'#65727b',strokeWidth:Math.max(1,edge.weight||1)},labelStyle:{fill:'#8b969d',fontSize:9},labelBgStyle:{fill:'#0c1013',fillOpacity:.9}})),[resource.data.edges]);
  return <div><PageHeader eyebrow="Relações do sistema" title="Mapa" description="Visualização direta das relações registradas. O mapa não infere conexões ocultas e não é um sistema semântico." actions={<button className="btn-secondary" onClick={resource.reload}><RefreshCw className="h-4 w-4"/> Atualizar</button>}/><DataModeBanner source={resource.source} error={resource.error} loading={resource.loading} onRetry={resource.reload}/><section className="panel overflow-hidden"><div className="panel-header"><div><p className="eyebrow mb-1">Grafo operacional</p><h2 className="text-sm font-semibold text-slate-200">{nodes.length} entidades · {edges.length} relações</h2></div><div className="hidden flex-wrap gap-1.5 sm:flex">{Object.keys(nodeColor).slice(0,5).map(type=><StatusBadge key={type} value={type}/>)}</div></div><div className="h-[calc(100vh-245px)] min-h-[520px] bg-ink-950"><ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{padding:.25}} minZoom={.25} maxZoom={1.8} proOptions={{hideAttribution:true}}><Background color="#222c33" gap={28} size={1}/><MiniMap nodeColor={(node)=>String(node.style?.borderColor||'#65727b')} maskColor="rgba(8,10,12,.7)" pannable zoomable/><Controls showInteractive={false}/></ReactFlow></div></section></div>;
}
