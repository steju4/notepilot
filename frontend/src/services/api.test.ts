import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("VITE_NOTEPILOT_HOSTED", "1");
  vi.stubGlobal("window", { dispatchEvent: vi.fn() });
  vi.stubGlobal(
    "CustomEvent",
    class extends Event {
      detail: unknown;
      constructor(name: string, options: { detail: unknown }) {
        super(name);
        this.detail = options.detail;
      }
    },
  );
  vi.stubGlobal("indexedDB", {
    open: vi.fn(() => {
      throw new Error("Hosted cache must remain unused");
    }),
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});
describe("private hosted instance", () => {
  it("does not store or retrieve offline scores", async () => {
    const { cachePut, cacheGet } = await import("./api");
    await cachePut("score", { secret: true });
    expect(await cacheGet("score")).toBeUndefined();
    expect(indexedDB.open).not.toHaveBeenCalled();
  });
  it("asks for the browser login after a Basic Auth challenge", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("login", { status: 401 })),
    );
    const { api } = await import("./api");
    await expect(api("/pieces")).rejects.toThrow("Anmeldung erforderlich");
    expect(indexedDB.open).not.toHaveBeenCalled();
  });
  it("never falls back to cached MusicXML after denied access", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("denied", { status: 401 })),
    );
    const { scoreXml } = await import("./api");
    await expect(scoreXml("private-id")).rejects.toThrow("erneut anmelden");
    expect(indexedDB.open).not.toHaveBeenCalled();
  });
  it("cannot open hosted scores offline", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("network unavailable");
      }),
    );
    const { api, scoreXml } = await import("./api");
    await expect(api("/pieces")).rejects.toThrow("Zugangsdaten erforderlich");
    await expect(scoreXml("private-id")).rejects.toThrow("konnte nicht geladen");
    expect(indexedDB.open).not.toHaveBeenCalled();
  });
});
