# Commands to Capture Class Transcript
When on a class page in Maven, where there is a transcript, run the following in the console to copy the transcript to the clipboard:

```
(async (copy) => {
  const vtts = [...new Set(performance.getEntriesByType('resource').map(e => e.name).filter(u => u.includes('.vtt') && !u.includes('storyboard')))];
  if (!vtts.length) return console.warn('no transcript .vtt seen yet — open the transcript panel / hit CC, then rerun');
  const raw = await fetch(vtts[0]).then(r => r.text());
  const text = raw.split('\n').filter(l => l.trim() && !/^WEBVTT/.test(l) && !/^\d+$/.test(l.trim()) && !l.includes('-->')).join(' ');
  copy(text);
  console.log(`${text.length} chars copied`);
})(copy);
```

If you'd rather have a file than a clipboard full of text, swap copy(text) for a Blob download, which avoids the Command Line API entirely:

```
(async (copy) => {
  const vtts = [...new Set(performance.getEntriesByType('resource').map(e => e.name).filter(u => u.includes('.vtt') && !u.includes('storyboard')))];
  if (!vtts.length) return console.warn('no transcript .vtt seen yet — open the transcript panel / hit CC, then rerun');
  const raw = await fetch(vtts[0]).then(r => r.text());
  const text = raw.split('\n').filter(l => l.trim() && !/^WEBVTT/.test(l) && !/^\d+$/.test(l.trim()) && !l.includes('-->')).join(' ');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], {type: 'text/plain'}));
    a.download = 'lecture.txt';
    a.click();
  console.log(`${text.length} chars copied`);
})(copy);
```
