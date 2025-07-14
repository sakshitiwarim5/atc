"use client";

import { useEffect, useState } from "react";
import api from "@/utils/api"; // Make sure this is correctly set

export default function Page() {
  const [aircrafts, setAircrafts] = useState([]);
  const [message, setMessage] = useState("");
  const [selectedAircraft, setSelectedAircraft] = useState(null);
  const [commandType, setCommandType] = useState("");
  const [commandValue, setCommandValue] = useState("");

  const fetchAircrafts = async () => {
    try {
      const res = await api.get("/aircrafts");
      setAircrafts(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const spawnAircraft = async () => {
    try {
      const res = await api.post("/aircrafts/spawn");
      setMessage(`✅ Spawned Aircraft: ${res.data.callsign}`);
      fetchAircrafts();
    } catch {
      setMessage("❌ Failed to spawn aircraft.");
    }
  };

  const removeAircraft = async () => {
    try {
      const res = await api.delete("/aircrafts/remove");
      setMessage(res.data.message);
      fetchAircrafts();
    } catch {
      setMessage("❌ Failed to remove aircraft.");
    }
  };

  const sendCommand = async () => {
    if (!selectedAircraft || !commandType) {
      setMessage("❌ Please select aircraft and command.");
      return;
    }
    try {
      const res = await api.post(`/aircrafts/${selectedAircraft}/command`, {
        command_type: commandType,
        value: commandValue ? parseInt(commandValue) : null,
      });
      setMessage(`✅ ${res.data.status} ${res.data.reason || ""}`);
      fetchAircrafts();
    } catch {
      setMessage("❌ Failed to send command.");
    }
  };

  useEffect(() => {
    fetchAircrafts();

    const ws = new WebSocket("ws://localhost:8000/ws/aircrafts"); // Update in prod

    ws.onmessage = (event) => {
      if (event.data === "refresh") {
        fetchAircrafts();
      }
    };

    ws.onerror = (e) => console.error("WebSocket error:", e);
    ws.onclose = () => console.log("WebSocket disconnected");

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-blue-50 text-black p-6">
      <h1 className="text-4xl font-bold text-center text-blue-800 mb-10">
        🛫 Air Traffic Control Dashboard
      </h1>

      <div className="flex flex-wrap justify-center gap-4 mb-8">
        <button
          onClick={spawnAircraft}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-5 py-2 rounded shadow-md transition"
        >
          ➕ Spawn Aircraft
        </button>
        <button
          onClick={removeAircraft}
          className="bg-red-600 hover:bg-red-700 text-white font-semibold px-5 py-2 rounded shadow-md transition"
        >
          ❌ Remove Random
        </button>
      </div>

      {message && (
        <div className="max-w-2xl mx-auto mb-6 bg-white border border-gray-300 text-center p-4 rounded shadow text-sm font-medium">
          {message}
        </div>
      )}

      <div className="overflow-x-auto shadow border border-gray-300 rounded-lg bg-white mb-10">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-blue-200 text-gray-700 uppercase text-xs sticky top-0 z-10">
            <tr>
              <th className="px-4 py-3">Callsign</th>
              <th className="px-4 py-3">Altitude</th>
              <th className="px-4 py-3">Speed</th>
              <th className="px-4 py-3">Heading</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {aircrafts.map((ac, idx) => (
              <tr
                key={ac.id}
                className={idx % 2 === 0 ? "bg-white" : "bg-gray-50"}
              >
                <td className="px-4 py-2 font-bold">{ac.callsign}</td>
                <td className="px-4 py-2">
                  {ac.current_altitude} → {ac.target_altitude}
                </td>
                <td className="px-4 py-2">
                  {ac.current_speed} → {ac.target_speed}
                </td>
                <td className="px-4 py-2">
                  {ac.current_heading} → {ac.target_heading}
                </td>
                <td className="px-4 py-2 capitalize font-medium text-blue-700">
                  {ac.status}
                </td>
                <td className="px-4 py-2 flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedAircraft(ac.callsign)}
                    className="bg-yellow-400 hover:bg-yellow-500 px-3 py-1 rounded text-xs font-medium"
                  >
                    🎯 Command
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedAircraft && (
        <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-lg border border-blue-200">
          <h2 className="text-2xl font-semibold mb-4 text-center text-blue-800">
            🎯 Command Aircraft: {selectedAircraft}
          </h2>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-1">
              Command Type
            </label>
            <select
              className="w-full border rounded px-3 py-2"
              value={commandType}
              onChange={(e) => setCommandType(e.target.value)}
            >
              <option value="">-- Select Command --</option>
              <option value="land">🛬 Land</option>
              <option value="take_off">🛫 Take Off</option>
              <option value="altitude_change">⬆️ Change Altitude</option>
              <option value="speed_change">🏎️ Change Speed</option>
              <option value="heading_change">🧭 Change Heading</option>
              <option value="emergency_land">🚨 Emergency Land</option>
              <option value="divert">🌪️ Divert</option>
              <option value="hold">⭕ Hold</option>
            </select>
          </div>

          {[
            "altitude_change",
            "speed_change",
            "heading_change",
            "divert",
          ].includes(commandType) && (
            <div className="mb-4">
              <label className="block text-sm font-semibold mb-1">Value</label>
              <input
                type="number"
                className="w-full border rounded px-3 py-2"
                value={commandValue}
                onChange={(e) => setCommandValue(e.target.value)}
                placeholder="Enter value"
              />
            </div>
          )}

          <button
            onClick={sendCommand}
            className="bg-blue-600 hover:bg-blue-700 text-white w-full py-2 rounded font-semibold transition"
          >
            🚀 Send Command
          </button>
        </div>
      )}
    </div>
  );
}
