import { useEffect, useState } from "react";
import type { Expediente } from "./types";
import SelloCard from "./components/SelloCard";
import SerieChart from "./components/SerieChart";
import PruebasTable from "./components/PruebasTable";

export default function App() {
  const [ids, setIds] = useState<string[]>([]);
  const [e, setE] = useState<Expediente | null>(null);
  useEffect(() => { fetch("/expedientes/index.json").then(r => r.json()).then(setIds); }, []);
  useEffect(() => { if (ids[0]) fetch(`/expedientes/${ids[0]}.json`).then(r => r.json()).then(setE); }, [ids]);
  return (
    <main style={{ maxWidth: 820, margin: "0 auto", padding: 16, fontFamily: "system-ui" }}>
      <h1>TerraVerdict</h1>
      <select onChange={ev => fetch(`/expedientes/${ev.target.value}.json`).then(r => r.json()).then(setE)}>
        {ids.map(i => <option key={i}>{i}</option>)}
      </select>
      {e && (<>
        <SelloCard e={e} />
        <PruebasTable e={e} />
        <SerieChart e={e} valores={Object.values(e.serie)} />
        {e.advertencias.map(a => <p key={a}>⚠️ {a}</p>)}
        <small>preregistro {e.procedencia.preregistro_sha256.slice(0, 12)} · entradas {e.procedencia.entradas_sha256.slice(0, 12)}</small>
      </>)}
    </main>
  );
}
