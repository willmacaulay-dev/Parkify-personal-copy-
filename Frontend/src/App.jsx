import { useEffect, useMemo, useRef, useState } from "react";
import ParkingMap from "./components/ParkingMap.jsx";
import Legend from "./components/Legend.jsx";
import "./App.css";

const ENV_BASE = import.meta.env.VITE_API_BASE ?? "";
const API_BASE = ENV_BASE || (import.meta.env.DEV ? "http://127.0.0.1:5000" : "");

export default function App() {
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState(null);

    const [garages, setGarages] = useState([]);
    const [updatedAt, setUpdatedAt] = useState(null);
    const [generatedAt, setGeneratedAt] = useState(null);

    const [selectedId, setSelectedId] = useState(null);

    const POLL_MS = 10000;
    const inFlightRef = useRef(false);

    async function fetchParking(signal) {
        if (inFlightRef.current) return;
        inFlightRef.current = true;

        const url = `${API_BASE}/parking`;

        try {
            setErr(null);

            const resp = await fetch(url, {
                method: "GET",
                signal,
                mode: "cors",
                cache: "no-store",
            });

            if (!resp.ok) {
                const txt = await resp.text().catch(() => "");
                throw new Error(`Request failed ${resp.status}: ${txt}`);
            }

            const data = await resp.json();

            const list = Array.isArray(data.garages) ? data.garages : [];
            setGarages(list);
            setUpdatedAt(data.updated_at ?? null);
            setGeneratedAt(list[0]?.generated_at ?? null);
            setLoading(false);
        } catch (e) {
            if (e?.name === "AbortError") return;
            setErr(e?.message ?? "Network error");
            setLoading(false);
        } finally {
            inFlightRef.current = false;
        }
    }

    useEffect(() => {
        const controller = new AbortController();

        fetchParking(controller.signal);

        const id = setInterval(() => {
            fetchParking(controller.signal);
        }, POLL_MS);

        return () => {
            clearInterval(id);
            controller.abort();
        };
    }, []);

    const selectedGarage = 
        useMemo(
            () => garages.find((g) => g.garage_id === selectedId) 
            ?? null, [garages, selectedId]
        );

    return (
        <div className="page">
            <div className="container">
                <h2>Madison Parking</h2>

                <div>
                    {loading && <span>Loading...</span>}
                    {err && <span>Error: {err}</span>}
                    {!loading && !err && <span>Connected</span>}
                </div>

                <div>
                    <span>Updated: {updatedAt ?? "-"}</span>
                    <span style={{ marginLeft: 12 }}>
                        Generated: {generatedAt ?? "-"}
                    </span>
                </div>

                <div style={{ marginTop: 10 }}>
                    <Legend />
                </div>

                <div style={{ marginTop: 10 }}>
                    <ParkingMap
                        garages={garages}
                        selectedId={selectedId}
                        onSelect={setSelectedId}
                    />
                </div>

                <div style={{ marginTop: 12 }}>
                <h3>Details</h3>

                {!selectedGarage ? (
                    <div>None selected</div>
                ) : (
                    <div>
                    <div>Name: {selectedGarage.name}</div>
                    <div>Available: {selectedGarage.available_now}</div>
                    <div>Occupied: {selectedGarage.occupied_now}</div>
                    <div>Capacity: {selectedGarage.capacity ?? "-"}</div>
                    <div>Predicted (30 min): {selectedGarage.predicted_30 ?? "-"}</div>
                    <div>Updated: {selectedGarage.updated_at ?? "-"}</div>
                    <div>Generated: {selectedGarage.generated_at ?? "-"}</div>
                    </div>
                )}
                </div>
            </div>
        </div>
    );
}
// c
