import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogTrigger, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'react-hot-toast';
import jsPDF from 'jspdf';

// API helper functions
async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const api = {
  // Patient
  fetchPatients: () => fetchJSON('/api/patients'),
  createPatient: data => fetchJSON('/api/patients', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) }),
  updatePatient: (id, data) => fetchJSON(`/api/patients/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) }),
  deletePatient: id => fetchJSON(`/api/patients/${id}`, { method: 'DELETE' }),
  fetchPatientSummary: id => fetchJSON(`/api/patients/${id}/summary`), // résumé derniers séjours
  // Intervention
  fetchInterventions: () => fetchJSON('/api/interventions'),
  createIntervention: data => fetchJSON('/api/interventions', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) }),
  updateIntervention: (id, data) => fetchJSON(`/api/interventions/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) }),
  deleteIntervention: id => fetchJSON(`/api/interventions/${id}`, { method: 'DELETE' }),
  computeScores: id => fetchJSON(`/api/interventions/${id}/scores`), // calcul scores Glasgow, NEWS, etc.
  exportHL7: id => fetchJSON(`/api/interventions/${id}/hl7`),
  exportPDF: id => fetchJSON(`/api/interventions/${id}/report`) // retourne PDF blob
};

export default function App() {
  const [tab, setTab] = useState<'dashboard'|'patients'|'interventions'>('dashboard');

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <header className="max-w-6xl mx-auto flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">DPI Web SMUR</h1>
        <nav className="space-x-4">
          <Button variant={tab==='dashboard'?'default':'outline'} onClick={()=>setTab('dashboard')}>Dashboard</Button>
          <Button variant={tab==='patients'?'default':'outline'} onClick={()=>setTab('patients')}>Patients</Button>
          <Button variant={tab==='interventions'?'default':'outline'} onClick={()=>setTab('interventions')}>Interventions</Button>
        </nav>
      </header>
      <main className="max-w-6xl mx-auto space-y-6">
        {tab==='dashboard' && <Dashboard />}
        {tab==='patients' && <PatientSection />}
        {tab==='interventions' && <InterventionSection />}
      </main>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({ patients:0, interventions:0 });
  useEffect(()=>{
    fetchJSON('/api/stats')
      .then(data=>setStats(data))
      .catch(()=>toast.error('Erreur chargement statistiques'));
  },[]);

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardContent>
          <h2 className="text-xl font-semibold">Patients</h2>
          <p className="text-3xl">{stats.patients}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <h2 className="text-xl font-semibold">Interventions</n2>
          <p className="text-3xl">{stats.interventions}</p>
        </CardContent>
      </Card>
    </div>
  );
}

function PatientSection() {
  const [patients, setPatients] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState(false);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [summaryPatient, setSummaryPatient] = useState(null);
  const [openSummary, setOpenSummary] = useState(false);

  useEffect(()=>{ loadPatients(); }, []);
  useEffect(()=>{ setFiltered(patients.filter(p => `${p.firstName} ${p.lastName}`.toLowerCase().includes(search.toLowerCase()))); }, [search, patients]);

  async function loadPatients() {
    try { setLoading(true); const data = await api.fetchPatients(); setPatients(data); }
    catch{toast.error('Erreur chargement patients')} finally{setLoading(false)}
  }
  async function handleDelete(id) {
    if(!confirm('Confirmer suppression ?')) return;
    try{ await api.deletePatient(id); toast.success('Patient supprimé'); loadPatients(); }
    catch{toast.error('Erreur suppression')}
  }
  async function viewSummary(id) {
    try{ const data = await api.fetchPatientSummary(id); setSummaryPatient(data); setOpenSummary(true);} 
    catch{toast.error('Erreur chargement résumé')}
  }

  return (
    <>
      <div className="flex justify-between items-center mb-4">
        <Input placeholder="Rechercher patient..." value={search} onChange={e=>setSearch(e.target.value)} />
        <Button onClick={()=>{setSelected(null); setOpenForm(true)}}>Nouveau patient</Button>
      </div>

      <Card>
        <CardContent>
          {loading ? <Spinner /> : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Nom</TableHeader>
                  <TableHeader>Prénom</TableHeader>
                  <TableHeader>Naissance</TableHeader>
                  <TableHeader>Actions</TableHeader>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map(p=>(
                  <TableRow key={p.id}>
                    <TableCell>{p.lastName}</TableCell>
                    <TableCell>{p.firstName}</TableCell>
                    <TableCell>{new Date(p.birthDate).toLocaleDateString()}</TableCell>
                    <TableCell className="space-x-2">
                      <Button size="sm" onClick={()=>{setSelected(p); setOpenForm(true)}}>Éditer</Button>
                      <Button size="sm" variant="outline" onClick={()=>viewSummary(p.id)}>Résumé</Button>
                      <Button size="sm" variant="destructive" onClick={()=>handleDelete(p.id)}>Suppr.</Button>
                      <Button size="sm" asChild>
                        <a href={`https://fhir.example.com/Patient/${p.id}`} target="_blank">FHIR</a>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Form Modal */}
      <Dialog open={openForm} onOpenChange={setOpenForm}>
        <DialogContent>
          <PatientForm patient={selected} onSuccess={()=>{setOpenForm(false); loadPatients();}} />
        </DialogContent>
      </Dialog>

      {/* Summary Modal */}
      <Dialog open={openSummary} onOpenChange={setOpenSummary}>
        <DialogContent>
          <DialogTitle>Résumé des derniers séjours</DialogTitle>
          <DialogDescription>
            {summaryPatient ? (
              <ul className="list-disc pl-5 space-y-2">
                {summaryPatient.map((s,i)=><li key={i}>{s.date}: {s.summary}</li>)}
              </ul>
            ) : <Spinner />}
          </DialogDescription>
        </DialogContent>
      </Dialog>
    </>
  );
}

function InterventionSection() {
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState(false);
  const [selected, setSelected] = useState(null);

  useEffect(()=>{ loadInterventions(); }, []);
  async function loadInterventions() {
    try{ setLoading(true); const data = await api.fetchInterventions(); setInterventions(data); }
    catch{toast.error('Erreur chargement')} finally{setLoading(false)}
  }
  async function handleDelete(id) {
    if(!confirm('Confirmer suppression ?')) return;
    try{ await api.deleteIntervention(id); toast.success('Supprimée'); loadInterventions(); }
    catch{toast.error('Erreur')}  }
  async function handleScore(id) {
    try{ const scores = await api.computeScores(id); toast(`Scores: G${scores.glasgow}, N${scores.news}`); }
    catch{toast.error('Erreur calcul scores')}
  }
  async function downloadPDF(id) {
    try{
      const blob = await api.exportPDF(id);
      const url = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a'); link.href = url; link.download = `intervention_${id}.pdf`; link.click();
    } catch{toast.error('Erreur génération PDF')}
  }
  async function downloadHL7(id) {
    try{
      const content = await api.exportHL7(id);
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = `intervention_${id}.hl7`; link.click();
    } catch{toast.error('Erreur export HL7')}
  }

  return (
    <>
      <div className="flex justify-end mb-4">
        <Button onClick={()=>{setSelected(null); setOpenForm(true)}}>Nouvelle intervention</Button>
      </div>
      <Card>
        <CardContent>
          {loading ? <Spinner /> : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Date</TableHeader>
                  <TableHeader>Lieu</TableHeader>
                  <TableHeader>Score</TableHeader>
                  <TableHeader>Actions</TableHeader>
                </TableRow>
              </TableHead>
              <TableBody>
                {interventions.map(i=>(
                  <TableRow key={i.id}>
                    <TableCell>{new Date(i.datetime).toLocaleString()}</TableCell>
                    <TableCell>{i.location}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={()=>handleScore(i.id)}>Voir</Button>
                    </TableCell>
                    <TableCell className="space-x-2">
                      <Button size="sm" onClick={()=>{setSelected(i); setOpenForm(true)}}>Éditer</Button>
                      <Button size="sm" variant="destructive" onClick={()=>handleDelete(i.id)}>Suppr.</Button>
                      <Button size="sm" variant="outline" onClick={()=>downloadPDF(i.id)}>PDF</Button>
                      <Button size="sm" variant="outline" onClick={()=>downloadHL7(i.id)}>HL7</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={openForm} onOpenChange={setOpenForm}>
        <DialogContent>
          <InterventionForm intervention={selected} onSuccess={()=>{setOpenForm(false); loadInterventions();}} />
        </DialogContent>
      </Dialog>
    </>
  );
}

function InterventionForm({ intervention, onSuccess }) {
  const isEdit = !!intervention;
  const [form, setForm] = useState({ datetime:'', location:'', notes:'' });
  useEffect(()=>{
    if(intervention) setForm({ datetime: intervention.datetime, location: intervention.location, notes: intervention.notes });
  },[intervention]);
  async function handleSubmit(e) {
    e.preventDefault();
    try{
      if(isEdit) await api.updateIntervention(intervention.id, form);
      else await api.createIntervention(form);
      toast.success(isEdit?'Mise à jour':'Créée');
      onSuccess();
    }catch{toast.error('Erreur sauvegarde')}
  }
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-xl font-semibold">{isEdit?'Modifier':'Nouvelle'} intervention</h3>
      <Input label="Date & Heure" type="datetime-local" value={form.datetime} onChange={e=>setForm({...form, datetime:e.target.value})} />
      <Input label="Lieu" value={form.location} onChange={e=>setForm({...form, location: e.target.value})} />
      <div>
        <label className="block text-sm font-medium">Observations</label>
        <textarea rows={4} className="mt-1 block w-full border-gray-300 rounded" value={form.notes} onChange={e=>setForm({...form, notes:e.target.value})} />
      </div>
      <div className="flex justify-end space-x-2">
        <Button variant="outline">Annuler</Button>
        <Button type="submit">Enregistrer</Button>
      </div>
    </form>
  );
}
