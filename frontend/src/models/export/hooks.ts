import { useMutation } from '@tanstack/react-query';
import { exportApi, saveExportedFile } from './service';
import type { ExportCatalogParams, ExportError, ExportedFile } from './schema';

export function useExportCatalog() {
  return useMutation<ExportedFile, ExportError, ExportCatalogParams>({
    mutationFn: (params) => exportApi.catalogCsv(params),
    onSuccess: saveExportedFile,
  });
}

export function useExportTracking() {
  return useMutation<ExportedFile, ExportError, void>({
    mutationFn: () => exportApi.trackingCsv(),
    onSuccess: saveExportedFile,
  });
}
