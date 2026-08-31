// Pré-validation côté client : on évite d'uploader (et de brûler un crédit)
// une vidéo trop lourde ou trop longue. Le backend re-vérifie de toute façon.

export const DEFAULT_LIMITS = { maxUploadMb: 50, maxVideoSeconds: 60 };

const readDuration = (file) =>
  new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement('video');
    el.preload = 'metadata';
    el.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(Number.isFinite(el.duration) ? el.duration : null);
    };
    el.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null); // illisible ici -> on laisse le backend trancher
    };
    el.src = url;
  });

export async function validateVideoFile(file, limits = DEFAULT_LIMITS) {
  const { maxUploadMb, maxVideoSeconds } = { ...DEFAULT_LIMITS, ...limits };

  if (file.size > maxUploadMb * 1024 * 1024) {
    const mb = (file.size / (1024 * 1024)).toFixed(1);
    return { ok: false, error: `Video too heavy (${mb} MB). Max ${maxUploadMb} MB.` };
  }

  const duration = await readDuration(file);
  if (duration !== null && duration > maxVideoSeconds) {
    return {
      ok: false,
      error: `Video too long (${Math.round(duration)}s). Max ${maxVideoSeconds}s — film a single set.`,
    };
  }

  return { ok: true };
}
