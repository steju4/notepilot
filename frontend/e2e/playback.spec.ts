import { test, expect } from "@playwright/test";
const xml = `<?xml version="1.0"?><score-partwise version="4.0"><part-list><score-part id="P1"><part-name>Tenorhorn</part-name></score-part></part-list><part id="P1">
<measure number="1"><attributes><divisions>1</divisions><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes><direction><sound tempo="120"/></direction><note><pitch><step>C</step><octave>4</octave></pitch><duration>3</duration><voice>1</voice><type>half</type><dot/><notations><tied type="start"/></notations></note></measure>
<measure number="2"><note><pitch><step>C</step><octave>4</octave></pitch><duration>3</duration><voice>1</voice><type>half</type><dot/><notations><tied type="stop"/></notations></note></measure>
<measure number="3"><note><pitch><step>D</step><octave>4</octave></pitch><duration>3</duration><voice>1</voice><type>half</type><dot/></note></measure></part></score-partwise>`;
test("sampled tenorhorn sustains the tie and crosses bars without added silence", async ({
  page,
  request,
}) => {
  const create = await request.post("/api/v1/pieces", {
    data: { title: "Taktgrenzen-Regression", instrument: "tenorhorn" },
  });
  const id = (await create.json()).id;
  await request.post(`/api/v1/pieces/${id}/documents`, {
    multipart: {
      file: { name: "tie.musicxml", mimeType: "application/xml", buffer: Buffer.from(xml) },
    },
  });
  await request.patch(`/api/v1/pieces/${id}`, { data: { playback_settings: { countIn: 0 } } });
  const score = await (await request.get(`/api/v1/pieces/${id}/score`)).json();
  expect(
    score.timeline.map((n: { start: number; duration: number }) => [n.start, n.duration]),
  ).toEqual([
    [0, 6],
    [6, 3],
  ]);
  await page.addInitScript(() => {
    const state = window as typeof window & { __levels: { time: number; rms: number }[] };
    state.__levels = [];
    const connect = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function (
      destination: AudioNode | AudioParam,
      output = 0,
      input = 0,
    ) {
      if (destination instanceof AudioDestinationNode) {
        const analyser = this.context.createAnalyser();
        analyser.fftSize = 2048;
        connect.call(this, analyser, output, 0);
        connect.call(analyser, destination, 0, input);
        const samples = new Float32Array(2048);
        setInterval(() => {
          analyser.getFloatTimeDomainData(samples);
          state.__levels.push({
            time: this.context.currentTime,
            rms: Math.sqrt(samples.reduce((s, v) => s + v * v, 0) / samples.length),
          });
        }, 10);
        return destination;
      }
      return destination instanceof AudioParam
        ? connect.call(this, destination, output)
        : connect.call(this, destination, output, input);
    } as typeof AudioNode.prototype.connect;
  });
  await page.goto(`/#piece/${id}`);
  await page.getByRole("button", { name: "Wiedergabe starten", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Wiedergabe pausieren", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Wiedergabe starten", exact: true })).toBeVisible({
    timeout: 12000,
  });
  const levels = await page.evaluate(
    () => (window as typeof window & { __levels: { time: number; rms: number }[] }).__levels,
  );
  const onset = levels.find((s) => s.rms > 0.001)!.time;
  for (const boundary of [1.5, 3]) {
    const around = levels.filter(
      (s) => s.time >= onset + boundary - 0.12 && s.time <= onset + boundary + 0.12,
    );
    expect(around.length).toBeGreaterThan(2);
    expect(around.filter((s) => s.rms < 0.00001).length).toBe(0);
  }
});
