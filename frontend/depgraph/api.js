export async function fetchSnapshot() {
  const response = await fetch("/api/depgraph/snapshot");
  if (!response.ok) {
    throw new Error(`Failed to fetch snapshot: ${response.status}`);
  }
  return response.json();
}

export function subscribeToSnapshotEvents(onSnapshot) {
  const source = new EventSource("/api/depgraph/events");
  source.addEventListener("snapshot", () => onSnapshot());
  source.onerror = () => {
    if (source.readyState === EventSource.CLOSED) {
      source.close();
    }
  };
  return () => source.close();
}
