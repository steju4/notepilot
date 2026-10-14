import { test, expect } from "@playwright/test";
import path from "node:path";

test("MusicXML import, rendering, correction, playback, practice, export and offline use", async ({
  page,
  request,
  context,
}, testInfo) => {
  const failures: string[] = [];
  page.on("pageerror", (error) => failures.push(error.message));
  await page.addInitScript(() => {
    const observed = window as typeof window & { __audioPeak: number };
    observed.__audioPeak = 0;
    const connect = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function (
      destination: AudioNode | AudioParam,
      output = 0,
      input = 0,
    ) {
      if (destination instanceof AudioDestinationNode) {
        const analyser = this.context.createAnalyser();
        analyser.fftSize = 256;
        connect.call(this, analyser, output, 0);
        connect.call(analyser, destination, 0, input);
        const samples = new Float32Array(256);
        setInterval(() => {
          analyser.getFloatTimeDomainData(samples);
          for (const value of samples)
            observed.__audioPeak = Math.max(observed.__audioPeak, Math.abs(value));
        }, 25);
        return destination;
      }
      return destination instanceof AudioParam
        ? connect.call(this, destination, output)
        : connect.call(this, destination, output, input);
    } as typeof AudioNode.prototype.connect;
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Deine Noten/ })).toBeVisible();
  await page.getByRole("button", { name: "Noten hinzufügen", exact: true }).click();
  await page
    .locator("input[type=file][multiple]")
    .setInputFiles(path.resolve("../examples/abend-am-fluss.musicxml"));
  await page.getByLabel("Titel des Stücks").fill(`Browser-Test ${testInfo.project.name}`);
  await page.getByRole("button", { name: /Importieren und prüfen/ }).click();
  await expect(
    page.getByRole("heading", { name: new RegExp(`Browser-Test ${testInfo.project.name}`) }),
  ).toBeVisible();
  await expect(page.locator(".score-svg svg")).toBeVisible();
  const id = await page.evaluate(() => location.hash.split("/")[1]);
  const scoreBefore = await (await request.get(`/api/v1/pieces/${id}/score`)).json();
  expect(scoreBefore.measure_count).toBe(4);
  await page.locator(".vf-notehead").first().click();
  await expect(page.getByRole("heading", { name: "C4 bearbeiten" })).toBeVisible();
  await page.getByRole("combobox", { name: "Ton", exact: true }).selectOption("F");
  await page.getByRole("combobox", { name: "Vorzeichen", exact: true }).selectOption("1");
  await page.getByRole("button", { name: "Änderung speichern", exact: true }).click();
  await expect(page.getByRole("heading", { name: "C4 bearbeiten" })).not.toBeVisible();
  await expect
    .poll(async () => {
      const r = await request.get(`/api/v1/pieces/${id}/score`);
      return (await r.json()).timeline[0].written_midi;
    })
    .toBe(66);
  await page.getByRole("button", { name: "Rückgängig", exact: true }).click();
  await expect
    .poll(async () => {
      const r = await request.get(`/api/v1/pieces/${id}/score`);
      return (await r.json()).timeline[0].written_midi;
    })
    .toBe(60);
  await page.getByRole("button", { name: "Wiederholen", exact: true }).click();
  await expect
    .poll(async () => {
      const r = await request.get(`/api/v1/pieces/${id}/score`);
      return (await r.json()).timeline[0].written_midi;
    })
    .toBe(66);
  await page.getByRole("combobox", { name: "Instrument", exact: true }).selectOption("trumpet");
  await expect
    .poll(async () => {
      const r = await request.get(`/api/v1/pieces/${id}/score`);
      return (await r.json()).timeline[0].sounding_midi;
    })
    .toBe(64);
  await page.getByRole("combobox", { name: "Einzähler", exact: true }).selectOption("0");
  await page.getByLabel("Tempogeschwindigkeit").fill("0.5");
  await page.getByRole("button", { name: "Wiedergabe starten", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Wiedergabe pausieren", exact: true }),
  ).toBeVisible();
  await expect.poll(() => page.locator("progress").getAttribute("value")).not.toBe("0");
  await expect
    .poll(() =>
      page.evaluate(() => (window as typeof window & { __audioPeak: number }).__audioPeak),
    )
    .toBeGreaterThan(0.001);
  await page.getByRole("button", { name: "Wiedergabe pausieren", exact: true }).click();
  await expect(page.getByText(/Pausiert · Durchlauf/)).toBeVisible();
  await page.getByRole("button", { name: "Wiedergabe stoppen", exact: true }).click();
  await page.getByLabel("Von Takt", { exact: true }).fill("2");
  await page.getByLabel("Bis Takt", { exact: true }).fill("3");
  await page.getByLabel("Passage wiederholen", { exact: true }).check();
  await page.getByLabel("Passage benennen", { exact: true }).fill("Schwierige Stelle");
  await page.getByRole("button", { name: "Passage speichern", exact: true }).click();
  await expect(page.getByRole("button", { name: /Schwierige Stelle Takt 2–3/ })).toBeVisible();
  const midi = await request.get(`/api/v1/pieces/${id}/export/midi`);
  expect((await midi.body()).subarray(0, 4).toString()).toBe("MThd");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "MusicXML exportieren", exact: true }).click();
  expect((await download).suggestedFilename()).toContain(".musicxml");
  await expect
    .poll(
      async () =>
        (await (await request.get(`/api/v1/pieces/${id}`)).json()).playback_settings.start,
    )
    .toBe(2);
  await expect
    .poll(
      async () =>
        (await (await request.get(`/api/v1/pieces/${id}`)).json()).playback_settings.speed,
    )
    .toBe(0.5);
  await page.reload();
  await expect(page.locator(".score-svg svg")).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Instrument", exact: true })).toHaveValue(
    "trumpet",
  );
  await expect(page.getByRole("button", { name: /Schwierige Stelle Takt 2–3/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByLabel("Tempogeschwindigkeit")).toHaveValue("0.5");
  await expect(page.getByLabel("Von Takt", { exact: true })).toHaveValue("2");
  await page.screenshot({ path: testInfo.outputPath("workspace.png"), fullPage: true });
  await page.evaluate(() => navigator.serviceWorker.ready.then(() => true));
  await context.setOffline(true);
  await page.reload();
  await expect(page.locator(".score-svg svg")).toBeVisible();
  await expect(
    page.getByText("Der lokale Server ist nicht erreichbar.", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Passage wiederholen", { exact: true }).uncheck();
  await page.getByRole("button", { name: "Wiedergabe starten", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Wiedergabe pausieren", exact: true }),
  ).toBeVisible();
  expect(failures).toEqual([]);
});
