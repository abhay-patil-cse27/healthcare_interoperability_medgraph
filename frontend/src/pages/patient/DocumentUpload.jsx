import { useState, useEffect, useRef } from "react";
import { Upload, FileText, Eye, Shield, CheckCircle2, AlertTriangle, Clock, Trash2, Download } from "lucide-react";
import toast from "react-hot-toast";
import { documentsAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";

function DocumentCard({ doc }) {
  const handleView = async () => {
    try {
      const { data } = await documentsAPI.downloadPdf(doc.document_id);
      const blob = new Blob([data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch {
      toast.error("Failed to load PDF");
    }
  };

  return (
    <div className="card p-5 hover:shadow-card-hover transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center">
            <FileText className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-sm font-medium text-surface-800 line-clamp-1">{doc.filename}</p>
            <p className="text-xs text-surface-400 mt-0.5">
              {doc.total_pages} pages · {doc.source_language}
              {doc.report_date && ` · ${doc.report_date}`}
            </p>
          </div>
        </div>
        <button onClick={handleView} className="btn-ghost text-xs flex items-center gap-1">
          <Eye className="w-3.5 h-3.5" /> View
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className="badge badge-green">
          <Shield className="w-3 h-3 mr-1" /> PHI Redacted
        </span>
        {doc.high_priority_sections > 0 && (
          <span className="badge badge-yellow">
            {doc.high_priority_sections} clinical notes
          </span>
        )}
        <span className="badge badge-blue">{doc.section_count} sections</span>
      </div>

      <p className="text-[10px] text-surface-400 mt-2">
        Uploaded {new Date(doc.uploaded_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
      </p>
    </div>
  );
}

export default function DocumentUpload() {
  const { user } = useAuthStore();
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => { loadDocuments(); }, []);

  const loadDocuments = async () => {
    setDocsLoading(true);
    try {
      const { data } = await documentsAPI.myDocuments();
      setDocuments(data);
    } catch { /* silent */ }
    finally { setDocsLoading(false); }
  };

  const handleUpload = async (file) => {
    if (!file) return;

    // Strict PDF-only validation (prevents injection attacks)
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Only PDF files are accepted. Other formats are blocked for security.");
      return;
    }
    if (file.type && file.type !== "application/pdf") {
      toast.error("Invalid file type. Only PDF documents are allowed.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      toast.error("File size exceeds 20MB limit");
      return;
    }

    setUploading(true);
    setUploadResult(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("patient_id", user.user_id);

    try {
      const { data } = await documentsAPI.upload(formData);
      setUploadResult(data);
      toast.success(`Document processed! ${data.sections_found} sections found.`);
      loadDocuments();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="page-title">My Lab Reports</h1>
        <p className="text-surface-500 text-sm mt-1">
          Upload PDF lab reports securely. Your data is encrypted and PHI-protected.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        className={`card p-8 border-2 border-dashed transition-colors cursor-pointer ${
          dragOver ? "border-brand-400 bg-brand-50" : "border-surface-200 hover:border-brand-300"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files[0])}
        />
        <div className="flex flex-col items-center text-center">
          {uploading ? (
            <>
              <Spinner size="lg" />
              <p className="text-sm text-surface-600 mt-3">Processing your report...</p>
              <p className="text-xs text-surface-400 mt-1">Extracting text, redacting PII, indexing clinical data</p>
            </>
          ) : (
            <>
              <div className="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center mb-3">
                <Upload className="w-7 h-7 text-brand-600" />
              </div>
              <p className="text-sm font-medium text-surface-700">Drop your PDF lab report here</p>
              <p className="text-xs text-surface-400 mt-1">or click to browse · Max 20MB · <span className="font-semibold text-surface-600">PDF only</span> (no images, docs, or other formats)</p>
              <div className="flex items-center gap-4 mt-4 text-xs text-surface-400">
                <span className="flex items-center gap-1"><Shield className="w-3 h-3 text-green-500" /> HIPAA Compliant</span>
                <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-blue-500" /> PHI Auto-Redacted</span>
                <span className="flex items-center gap-1"><FileText className="w-3 h-3 text-purple-500" /> FHIR Compatible</span>
              </div>
              <p className="text-[10px] text-surface-400 mt-3 max-w-sm">
                For security, only PDF documents are accepted. Your original file is stored encrypted and never modified.
              </p>
            </>
          )}
        </div>
      </div>

      {/* Upload Result */}
      {uploadResult && (
        <div className="card p-5 border-l-4 border-l-green-500 animate-slide-up">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium text-surface-800">Upload Successful</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="bg-surface-50 rounded-lg p-3">
              <p className="text-surface-400">Pages</p>
              <p className="text-lg font-semibold text-surface-800">{uploadResult.total_pages}</p>
            </div>
            <div className="bg-surface-50 rounded-lg p-3">
              <p className="text-surface-400">Sections</p>
              <p className="text-lg font-semibold text-surface-800">{uploadResult.sections_found}</p>
            </div>
            <div className="bg-surface-50 rounded-lg p-3">
              <p className="text-surface-400">PHI Redacted</p>
              <p className="text-lg font-semibold text-green-600">{uploadResult.privacy?.redactions_applied}</p>
            </div>
            <div className="bg-surface-50 rounded-lg p-3">
              <p className="text-surface-400">Indexed</p>
              <p className="text-lg font-semibold text-brand-600">{uploadResult.ingestion?.chunks_successful}</p>
            </div>
          </div>
          {uploadResult.privacy?.redacted_fields?.length > 0 && (
            <p className="text-xs text-surface-400 mt-3">
              <Shield className="w-3 h-3 inline mr-1 text-green-500" />
              Redacted: {uploadResult.privacy.redacted_fields.join(", ")}
            </p>
          )}
        </div>
      )}

      {/* Document History */}
      <div>
        <h2 className="section-title mb-3">Document History</h2>
        {docsLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : documents.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No documents yet"
            description="Upload your first lab report to get started"
          />
        ) : (
          <div className="grid gap-3">
            {documents.map((doc) => (
              <DocumentCard key={doc.document_id} doc={doc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
