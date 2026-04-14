import { Storage } from "@google-cloud/storage";
import Papa from "papaparse";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { BQ_PROJECT, PREDICTIONS_BUCKET } from "./constants";

let storage: Storage | undefined;

export function getStorageClient(): Storage {
  if (!storage) {
    storage = new Storage({ projectId: BQ_PROJECT });
  }
  return storage;
}

export async function downloadText(
  bucket: string,
  remotePath: string,
): Promise<string> {
  const localDir = process.env.PREDICTIONS_LOCAL_DIR;
  if (localDir) {
    const file = path.join(
      localDir,
      remotePath.startsWith("predictions/")
        ? remotePath.replace(/^predictions\//, "")
        : remotePath,
    );
    return readFile(file, "utf-8");
  }
  const [buf] = await getStorageClient()
    .bucket(bucket)
    .file(remotePath)
    .download();
  return buf.toString("utf-8");
}

export async function readCsvFromBucket<T>(
  remotePath: string,
  { bucket = PREDICTIONS_BUCKET }: { bucket?: string } = {},
): Promise<T[]> {
  const text = await downloadText(bucket, remotePath);
  const parsed = Papa.parse<T>(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
  if (parsed.errors.length > 0) {
    const first = parsed.errors[0];
    throw new Error(
      `CSV parse error in gs://${bucket}/${remotePath} at row ${first.row}: ${first.message}`,
    );
  }
  return parsed.data;
}
