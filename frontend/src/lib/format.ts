export function formatBytes(value?: number | null): string {
  const bytes = Number(value || 0);
  if (bytes <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / 1024 ** index;
  return `${size >= 10 || index === 0 ? size.toFixed(0) : size.toFixed(2)} ${units[index]}`;
}

export function formatDateTime(value?: number | null): string {
  if (!value || value <= 0) {
    return "长期有效";
  }
  const date = new Date(value * 1000);
  const pad = (item: number) => item.toString().padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function formatMoney(value?: number | null, symbol = "¥"): string {
  return `${symbol}${((value || 0) / 100).toFixed(2)}`;
}

export function percent(used: number, total: number): number {
  if (!total || total <= 0) {
    return 0;
  }
  return Math.min(Math.max(Math.round((used / total) * 100), 0), 100);
}
