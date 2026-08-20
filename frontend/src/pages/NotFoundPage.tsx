import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function NotFoundPage(){return <div className="panel mx-auto mt-20 max-w-xl p-8 text-center"><p className="eyebrow">404</p><h1 className="mt-3 text-2xl font-semibold text-slate-100">Rota não encontrada</h1><p className="mt-2 text-sm text-slate-500">Esta área não faz parte do cockpit atual.</p><Link to="/" className="btn-primary mt-6"><ArrowLeft className="h-4 w-4"/> Voltar para Hoje</Link></div>}
