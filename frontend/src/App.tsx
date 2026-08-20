import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './components/AppShell';
import TodayPage from './pages/TodayPage';
import DashboardPage from './pages/DashboardPage';
import DecisionsPage from './pages/DecisionsPage';
import ProjectsPage from './pages/ProjectsPage';
import GoalsPage from './pages/GoalsPage';
import HypothesesPage from './pages/HypothesesPage';
import MapPage from './pages/MapPage';
import JournalPage from './pages/JournalPage';
import OraclePage from './pages/OraclePage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App(){
  return <Routes><Route element={<AppShell/>}><Route index element={<TodayPage/>}/><Route path="painel" element={<DashboardPage/>}/><Route path="decisoes" element={<DecisionsPage/>}/><Route path="projetos" element={<ProjectsPage/>}/><Route path="metas" element={<GoalsPage/>}/><Route path="hipoteses" element={<HypothesesPage/>}/><Route path="mapa" element={<MapPage/>}/><Route path="diario" element={<JournalPage/>}/><Route path="oraculo" element={<OraclePage/>}/><Route path="configuracoes" element={<SettingsPage/>}/><Route path="hoje" element={<Navigate to="/" replace/>}/><Route path="*" element={<NotFoundPage/>}/></Route></Routes>;
}
