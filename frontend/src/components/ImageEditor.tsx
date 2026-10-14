import { useState } from "react";
import { RotateCcw, X } from "lucide-react";
import { patch } from "../services/api";
import type { Page, Detail } from "../types";
export function ImageEditor({
  page,
  onClose,
  onSave,
  onError,
}: {
  page: Page;
  onClose: () => void;
  onSave: (d: Detail) => void;
  onError: (message: string) => void;
}) {
  const [rotate, setRotate] = useState(0),
    [contrast, setContrast] = useState(1),
    [brightness, setBrightness] = useState(0),
    [bw, setBw] = useState(false),
    [deskew, setDeskew] = useState(false),
    [crop, setCrop] = useState([0, 0, 1, 1]),
    [perspective, setPerspective] = useState<number[][]>([]),
    [perspectiveMode, setPerspectiveMode] = useState(false),
    [busy, setBusy] = useState(false);
  const save = async (reset = false) => {
    setBusy(true);
    try {
      const result = await patch<Detail>(
        `/pages/${page.id}`,
        reset
          ? { reset: true }
          : {
              options: {
                rotate,
                contrast,
                brightness,
                black_white: bw,
                deskew,
                crop,
                perspective: perspective.length === 4 ? perspective : null,
              },
            },
      );
      onSave(result);
      onClose();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="modal-backdrop">
      <section className="modal wide" role="dialog" aria-modal="true" aria-labelledby="image-title">
        <button
          className="icon-button modal-close"
          aria-label="Bildbearbeitung schließen"
          onClick={onClose}
        >
          <X size={20} />
        </button>
        <h2 id="image-title">Aufnahme verbessern</h2>
        <p>
          Alle Korrekturen verwenden das erhaltene Original. Du kannst es jederzeit
          wiederherstellen.
        </p>
        <div className="image-edit-layout">
          <div
            className="image-preview"
            onClick={(e) => {
              if (!perspectiveMode || perspective.length === 4) return;
              const r = e.currentTarget.getBoundingClientRect();
              setPerspective((old) => [
                ...old,
                [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height],
              ]);
            }}
          >
            <img
              src={`/api/v1/pages/${page.id}/image?original=true`}
              alt="Originalaufnahme"
              style={{
                filter: `brightness(${1 + brightness / 100}) contrast(${contrast}) grayscale(${bw ? 1 : 0})`,
                transform: `rotate(${rotate}deg)`,
              }}
            />
            {perspective.map((p, i) => (
              <span
                className="corner"
                style={{ left: `${p[0] * 100}%`, top: `${p[1] * 100}%` }}
                key={i}
              >
                {i + 1}
              </span>
            ))}
          </div>
          <div>
            <label>
              Drehen · {rotate}°
              <input
                type="range"
                min={-180}
                max={180}
                value={rotate}
                onChange={(e) => setRotate(+e.target.value)}
              />
            </label>
            <label>
              Kontrast · {contrast.toFixed(1)}
              <input
                type="range"
                min={0.25}
                max={3}
                step={0.05}
                value={contrast}
                onChange={(e) => setContrast(+e.target.value)}
              />
            </label>
            <label>
              Helligkeit · {brightness}
              <input
                type="range"
                min={-100}
                max={100}
                value={brightness}
                onChange={(e) => setBrightness(+e.target.value)}
              />
            </label>
            <label className="check">
              <input type="checkbox" checked={bw} onChange={(e) => setBw(e.target.checked)} />
              Schwarz-Weiß-Optimierung
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={deskew}
                onChange={(e) => setDeskew(e.target.checked)}
              />
              Notenzeilen automatisch ausrichten
            </label>
            <details>
              <summary>Zuschneiden</summary>
              {["Links", "Oben", "Breite", "Höhe"].map((name, i) => (
                <label key={name}>
                  {name} (%)
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    value={Math.round(crop[i] * 100)}
                    onChange={(e) =>
                      setCrop((old) => old.map((v, n) => (n === i ? +e.target.value / 100 : v)))
                    }
                  />
                </label>
              ))}
            </details>
            <button
              className="secondary full"
              onClick={() => {
                setPerspectiveMode(!perspectiveMode);
                setPerspective([]);
              }}
            >
              {perspectiveMode ? "Ecken zurücksetzen" : "Perspektive korrigieren"}
            </button>
            {perspectiveMode && (
              <p className="small">
                Klicke die vier Ecken in dieser Reihenfolge: oben links, oben rechts, unten rechts,
                unten links. {perspective.length}/4
              </p>
            )}
          </div>
        </div>
        <div className="button-row end">
          <button className="secondary" disabled={busy} onClick={() => save(true)}>
            <RotateCcw size={16} />
            Original wiederherstellen
          </button>
          <button
            className="primary"
            disabled={busy || (perspectiveMode && perspective.length !== 4)}
            onClick={() => save()}
          >
            Korrektur speichern
          </button>
        </div>
      </section>
    </div>
  );
}
