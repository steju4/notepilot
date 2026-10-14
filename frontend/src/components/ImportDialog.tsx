import { useRef, useState } from "react";
import { Camera, FileUp, Music2, X, ArrowUp, ArrowDown, Trash2, LoaderCircle } from "lucide-react";
import { api, post } from "../services/api";
import type { Piece, Detail } from "../types";
export function ImportDialog({
  hosted = false,
  onClose,
  onImported,
  onError,
}: {
  hosted?: boolean;
  onClose: () => void;
  onImported: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [files, setFiles] = useState<File[]>([]),
    [title, setTitle] = useState(""),
    [busy, setBusy] = useState(false),
    [step, setStep] = useState("");
  const picker = useRef<HTMLInputElement>(null),
    camera = useRef<HTMLInputElement>(null);
  const add = (incoming: FileList | null) => {
    if (!incoming) return;
    const incomingFiles = Array.from(incoming);
    setFiles((old) => [...old, ...incomingFiles]);
    if (!title) setTitle(incomingFiles[0]?.name.replace(/\.[^.]+$/, "") ?? "");
  };
  const submit = async () => {
    if (!files.length || !title.trim()) return;
    setBusy(true);
    let created: Piece | undefined;
    try {
      created = await post<Piece>("/pieces", { title: title.trim() });
      for (let i = 0; i < files.length; i++) {
        setStep(`Datei ${i + 1} von ${files.length} wird lokal importiert`);
        const body = new FormData();
        body.append("file", files[i]);
        await api<Detail>(`/pieces/${created.id}/documents`, {
          method: "POST",
          body,
        });
      }
      onImported(created.id);
    } catch (e) {
      onError((e as Error).message);
      if (created) onImported(created.id);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="modal-backdrop">
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="import-title">
        <button
          className="icon-button modal-close"
          aria-label="Import schließen"
          onClick={onClose}
          disabled={busy}
        >
          <X size={20} />
        </button>
        <span className="eyebrow">DEINE MUSIK. DEIN TEMPO.</span>
        <h2 id="import-title">Neue Noten hinzufügen</h2>
        <p>
          Ein Foto, ein PDF oder eine digitale Partitur.{" "}
          {hosted
            ? "Deine Dateien werden auf den Testserver hochgeladen."
            : "Deine Dateien bleiben auf deinem Computer."}
        </p>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (!busy) add(e.dataTransfer.files);
          }}
        >
          <div className="round-icon">
            <FileUp size={30} />
          </div>
          <h3>Ziehe deine Noten hierher</h3>
          <p>JPG, PNG, WebP, PDF, MusicXML oder MXL · bis 40 MB</p>
          <div className="button-row">
            <button className="primary" onClick={() => picker.current?.click()} disabled={busy}>
              Dateien auswählen
            </button>
            <button className="secondary" onClick={() => camera.current?.click()} disabled={busy}>
              <Camera size={17} />
              Foto aufnehmen
            </button>
          </div>
        </div>
        <input
          ref={picker}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.pdf,.xml,.musicxml,.mxl"
          multiple
          hidden
          onChange={(e) => {
            add(e.target.files);
            e.target.value = "";
          }}
        />
        <input
          ref={camera}
          type="file"
          accept="image/*"
          capture="environment"
          hidden
          onChange={(e) => {
            add(e.target.files);
            e.target.value = "";
          }}
        />
        {files.length > 0 && (
          <>
            <label>
              Titel des Stücks
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                disabled={busy}
              />
            </label>
            <div className="file-list">
              {files.map((file, i) => (
                <div className="file-row" key={i}>
                  <Music2 size={18} />
                  <span>
                    {file.name}
                    <small>{(file.size / 1024 / 1024).toFixed(1)} MB</small>
                  </span>
                  <button
                    className="icon-button"
                    aria-label={`Datei ${i + 1} nach oben`}
                    disabled={busy || i === 0}
                    onClick={() =>
                      setFiles((old) => {
                        const a = [...old];
                        [a[i - 1], a[i]] = [a[i], a[i - 1]];
                        return a;
                      })
                    }
                  >
                    <ArrowUp size={16} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={`Datei ${i + 1} nach unten`}
                    disabled={busy || i === files.length - 1}
                    onClick={() =>
                      setFiles((old) => {
                        const a = [...old];
                        [a[i + 1], a[i]] = [a[i], a[i + 1]];
                        return a;
                      })
                    }
                  >
                    <ArrowDown size={16} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={`Datei ${i + 1} entfernen`}
                    disabled={busy}
                    onClick={() => setFiles((old) => old.filter((_, index) => index !== i))}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
            <button className="primary full" disabled={busy || !title.trim()} onClick={submit}>
              {busy ? (
                <>
                  <LoaderCircle className="spin" size={17} />
                  {step}
                </>
              ) : (
                <>
                  Importieren und prüfen <span>→</span>
                </>
              )}
            </button>
          </>
        )}
        <p className="muted small">
          MusicXML öffnet sich direkt. Fotos und PDFs werden anschließend mit der lokalen KI
          erkannt.
        </p>
      </section>
    </div>
  );
}
