export interface Statement {
  id: string;
  participant_id: string;
  year: number;
  month: number;
  statement_period: string;
  gcs_pdf_path: string;
  download_url: string;
  invoice_count: number;
  total_amount: string;
  generated_at: string;
  emailed_at: string | null;
}
