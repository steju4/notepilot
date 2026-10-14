let database: Promise<IDBDatabase> | null = null;
const hosted = import.meta.env.VITE_NOTEPILOT_HOSTED === "1";
function openStore() {
  if (!database)
    database = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open("notepilot-local", 1);
      request.onupgradeneeded = () => request.result.createObjectStore("cache");
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  return database;
}
export async function cachePut(key: string, value: unknown) {
  if (hosted) return;
  try {
    const db = await openStore();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("cache", "readwrite");
      tx.objectStore("cache").put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    /* Storage denial does not prevent online use. */
  }
}
export async function cacheGet<T>(key: string): Promise<T | undefined> {
  if (hosted) return undefined;
  try {
    const db = await openStore();
    return await new Promise<T | undefined>((resolve, reject) => {
      const req = db.transaction("cache").objectStore("cache").get(key);
      req.onsuccess = () => resolve(req.result as T);
      req.onerror = () => reject(req.error);
    });
  } catch {
    return undefined;
  }
}
export async function cacheClear() {
  try {
    const db = await openStore();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("cache", "readwrite");
      tx.objectStore("cache").clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    /* Cache is optional. */
  }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = "/api/v1" + path,
    read = !options.method || options.method === "GET";
  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...options.headers,
      },
      signal: options.signal ?? AbortSignal.timeout(35000),
    });
  } catch {
    window.dispatchEvent(new CustomEvent("backend-status", { detail: false }));
    if (read) {
      const stored = await cacheGet<T>(url);
      if (stored !== undefined) return stored;
    }
    throw new Error(
      hosted
        ? "Server nicht erreichbar oder Anmeldung abgelaufen. Bitte die Seite neu laden und erneut anmelden."
        : "Der lokale NotePilot-Server ist nicht erreichbar. Starte ihn auf deinem Computer. Bereits geöffnete Stücke kannst du offline abspielen.",
    );
  }
  window.dispatchEvent(new CustomEvent("backend-status", { detail: true }));
  if (
    hosted &&
    (response.status === 403 ||
      response.redirected ||
      response.headers.get("content-type")?.includes("text/html"))
  ) {
    throw new Error(
      "Anmeldung erforderlich. Bitte die Seite neu laden und bei Cloudflare Access anmelden.",
    );
  }
  if (!response.ok) {
    let error = "Die Anfrage konnte nicht verarbeitet werden.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") error = body.detail;
    } catch {
      /* Non-JSON proxy response. */
    }
    throw new Error(error);
  }
  if (response.status === 204) return undefined as T;
  const result = (await response.json()) as T;
  if (read) await cachePut(url, result);
  return result;
}
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
export const patch = <T>(path: string, body: unknown, options: RequestInit = {}) =>
  api<T>(path, { ...options, method: "PATCH", body: JSON.stringify(body) });
export async function scoreXml(id: string): Promise<string> {
  const key = "/api/v1/pieces/" + id + "/export/musicxml";
  let response: Response;
  try {
    response = await fetch(key, { signal: AbortSignal.timeout(10000) });
  } catch {
    const stored = await cacheGet<string>(key);
    if (stored) return stored;
    throw new Error("Die digitale Notenansicht konnte nicht geladen werden.");
  }
  if (
    !response.ok ||
    response.redirected ||
    response.headers.get("content-type")?.includes("text/html")
  ) {
    throw new Error(
      hosted
        ? "Bitte die Seite neu laden und erneut anmelden."
        : "Die digitale Notenansicht konnte nicht geladen werden.",
    );
  }
  const xml = await response.text();
  await cachePut(key, xml);
  return xml;
}
export function download(data: Blob, name: string) {
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
