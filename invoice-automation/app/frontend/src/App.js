import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import Sidebar from "./components/Sidebar";

const API_URL =
  process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://127.0.0.1:8000/api"
    : "/api");

const api = axios.create({ baseURL: API_URL });

function App() {


  const [activePage, setActivePage] =
    useState("dashboard");


  const [selectedFile, setSelectedFile] =
    useState(null);

  const [uploadStatus, setUploadStatus] =
    useState("No file selected");

  const [invoices, setInvoices] =
    useState([]);

  const [searchTerm, setSearchTerm] =
    useState("");

  const [viewMode, setViewMode] = useState("table");

  // HANDLE 

  const handleFileChange = (event) => {

    const file = event.target.files[0];

    if (file) {

      setSelectedFile(file);

      setUploadStatus(
        `Ready to upload: ${file.name}`
      );

    } else {

      setSelectedFile(null);

      setUploadStatus(
        "No file selected"
      );
    }
  };

  const fetchInvoices = useCallback(async () => {
    try {
      const res = await api.get("/invoices");
      setInvoices(
        res.data.map((invoice) => ({
          ...invoice,
          amount: parseAmount(invoice.amount),
        }))
      );
    } catch (err) {
      console.error("Failed to load invoices:", err);
    }
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const parseAmount = (value) => {
    const raw = String(value || "");
    const matches = [...raw.matchAll(/([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)/g)];
    if (matches.length === 0) return 0;
    const lastMatch = matches[matches.length - 1][1];
    return Number(lastMatch.replace(/,/g, "")) || 0;
  };

  const formatCurrency = (value) => {
    const amount = Number(value || 0);
    if (Number.isNaN(amount)) return "₹0";
    return `₹${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTaxValue = (value) => {
    let raw = String(value || "").trim();
    if (!raw) return "-";
    raw = raw.replace(/^(₹|Rs\.?|INR\.?)\s*/i, "").trim();
    return raw.endsWith("%") ? raw : `₹${raw}`;
  };

  const handleDeleteInvoice = async (invoiceId) => {
    try {
      await api.delete(`/invoices/${invoiceId}`);
      setInvoices((prev) => prev.filter((invoice) => invoice.id !== invoiceId));
    } catch (err) {
      console.error("Failed to delete invoice:", err);
      setUploadStatus("Unable to delete invoice. Try again.");
    }
  };

  const handleEditInvoice = async (invoice) => {
    const vendor = window.prompt("Vendor", invoice.vendor) ?? invoice.vendor;
    const invoice_number = window.prompt("Invoice", invoice.invoice_number) ?? invoice.invoice_number;
    const amountInput = window.prompt("Amount", invoice.amount) ?? invoice.amount;
    const date = window.prompt("Date", invoice.date) ?? invoice.date;

    try {
      const res = await api.put(`/invoices/${invoice.id}`, {
        vendor,
        invoice_number,
        amount: String(amountInput),
        date,
      });
      setInvoices((prev) =>
        prev.map((item) =>
          item.id === invoice.id
            ? { ...item, ...res.data, amount: parseAmount(res.data.amount) }
            : item
        )
      );
      setUploadStatus("Invoice updated successfully.");
    } catch (err) {
      console.error("Failed to update invoice:", err);
      setUploadStatus("Unable to update invoice. Try again.");
    }
  };


  const handleUploadClick = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a file first.");
      return;
    }

    setUploadStatus("Processing invoice with OCR...");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await api.post("/upload", formData);

      const uploadedInvoice = {
        ...res.data,
        amount: parseAmount(res.data.amount),
      };

      setInvoices((prevInvoices) => [uploadedInvoice, ...prevInvoices]);
      setUploadStatus(`${selectedFile.name} uploaded successfully`);
      setSelectedFile(null);
      setActivePage("invoices");
    } catch (err) {
      console.error("Upload failed:", err);
      setUploadStatus("Upload failed. Please try again.");
    }
  };

  

  const totalInvoices =
    invoices.length;

  const totalRevenue =
    invoices.reduce(

      (total, invoice) =>
        total + invoice.amount,

      0
    );

  const processedInvoices =
    invoices.filter(
      (invoice) =>
        invoice.status === "Processed"
    ).length;



  const filteredInvoices =
    invoices.filter((invoice) => {
      const vendor = (invoice.vendor || "").toLowerCase();
      const invNum = (invoice.invoice_number || "").toLowerCase();
      const term = searchTerm.toLowerCase();
      return vendor.includes(term) || invNum.includes(term);
    });

 
  const displayedInvoices = (searchTerm && filteredInvoices.length > 0) ? filteredInvoices : invoices;

  const graphData = displayedInvoices.reduce((acc, invoice) => {
    const label = invoice.vendor || "Unknown";
    acc[label] = (acc[label] || 0) + Number(invoice.amount || 0);
    return acc;
  }, {});

  const graphItems = Object.entries(graphData).sort((a, b) => b[1] - a[1]);
  const maxGraphValue = Math.max(...graphItems.map(([, value]) => value), 1);

  return (

    <div className="flex min-h-screen bg-slate-950 text-white">

      {/* SIDEBAR */}

      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />

      {/* MAIN */}

      <main className="flex-1 p-8">

        <div className="max-w-7xl mx-auto">

          {/* HEADER */}

          <div className="mb-10 landing-hero">

            <h1 className="text-5xl font-bold text-cyan-400">

              Invoice Dashboard

            </h1>

            <p className="mt-3 text-slate-400">

              Upload invoices and manage
              real-time invoice analytics.

            </p>

          </div>

          {/* DASHBOARD */}

          {activePage === "dashboard" && (

            <div key="dashboard" className="page-animate">

              <div className="space-y-6">

              {/* STATS */}

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">

                {/* TOTAL */}

                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl stat-card-anim delay-1 hover:bg-slate-800 transition-colors">

                  <p className="text-slate-400">
                    Total Invoices
                  </p>

                  <h2 className="text-4xl font-bold mt-3 animate-pulse">

                    {totalInvoices}

                  </h2>

                </div>

                {/* REVENUE */}

                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl stat-card-anim delay-2 hover:bg-slate-800 transition-colors">

                  <p className="text-slate-400">
                    Revenue
                  </p>

                  <h2 className="text-4xl font-bold mt-3 animate-pulse">

                    {formatCurrency(totalRevenue)}

                  </h2>

                </div>

                {/* PROCESSED */}

                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl stat-card-anim delay-3 hover:bg-slate-800 transition-colors">

                  <p className="text-slate-400">
                    Processed
                  </p>

                  <h2 className="text-4xl font-bold mt-3 text-green-400 animate-pulse">

                    {processedInvoices}

                  </h2>

                </div>

                {/* PENDING */}

                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl stat-card-anim delay-4 hover:bg-slate-800 transition-colors">

                  <p className="text-slate-400">
                    Pending
                  </p>

                  <h2 className="text-4xl font-bold mt-3 text-yellow-400 animate-pulse">

                    0

                  </h2>

                </div>

              </div>

              {/* RECENT ACTIVITY */}

              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">

                <h2 className="text-2xl font-semibold">

                  Recent Activity

                </h2>

                <div className="mt-6 space-y-4">

                  {invoices.length === 0 && (

                    <div className="py-16 text-center">

                      <h2 className="text-2xl font-semibold text-slate-400">

                        No invoices uploaded

                      </h2>

                      <p className="mt-3 text-slate-500">

                        Upload your first invoice
                        to begin processing.

                      </p>

                    </div>

                  )}

                  {invoices.map((invoice, index) => (

                    <div
                      key={index}
                      className="border-b border-slate-800 pb-4"
                    >

                      <div className="flex items-center justify-between">

                        <div>

                          <p className="font-medium">

                            {invoice.vendor}

                          </p>

                          <p className="text-sm text-slate-400">

                            {invoice.date}

                          </p>

                        </div>

                        <span className="text-green-400">

                          {invoice.status}

                        </span>

                      </div>

                      <div className="mt-3 flex gap-4 text-sm text-slate-400">
                        <span>SGST: {formatTaxValue(invoice.sgst)}</span>
                        <span>CGST: {formatTaxValue(invoice.cgst)}</span>
                        <span>IGST: {formatTaxValue(invoice.igst)}</span>
                      </div>

                    </div>

                  ))}

                </div>

              </div>

            </div>

          </div>

          )}

          {/* UPLOAD */}

          {activePage === "upload" && (

            <div key="upload" className="page-animate">

              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">

              <h2 className="text-3xl font-bold">

                Upload Invoice

              </h2>

              <p className="mt-3 text-slate-400">

                Upload PDF or image invoices
                for OCR processing.

              </p>

              {/* UPLOAD BOX */}

              <div className="mt-8 border-2 border-dashed border-cyan-500 rounded-3xl p-10 text-center">

                <input
                  key={
                    selectedFile
                      ? selectedFile.name
                      : "empty"
                  }
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.md"
                  onChange={handleFileChange}
                  className="w-full text-slate-300"
                />

                <button
                  onClick={handleUploadClick}
                  className="mt-6 bg-cyan-500 text-slate-950 font-semibold px-8 py-3 rounded-2xl hover:bg-cyan-400 transition"
                >

                  Upload Invoice

                </button>

                <p
                  className={`

                    mt-5
                    font-medium

                    ${
                      uploadStatus.includes("successfully")

                      ? "text-green-400"

                      : "text-slate-400"
                    }

                  `}
                >

                  {uploadStatus}

                </p>

              </div>

            </div>

          </div>

          )}

          {/* INVOICES / TABLES */}

          {(activePage === "invoices" || activePage === "tables") && (

            <div key="invoices" className="page-animate">

              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">

              <div className="flex items-center justify-between">

                <h2 className="text-3xl font-bold">

                  Uploaded Invoices

                </h2>

                {/* SEARCH */}

                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Search invoices..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-2xl px-4 py-2 outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={fetchInvoices}
                    className="bg-slate-700 text-slate-100 px-4 py-2 rounded-2xl hover:bg-slate-600 transition"
                  >
                    Refresh
                  </button>
                  <button
                    onClick={() => setViewMode((mode) => mode === "table" ? "graph" : "table")}
                    className="bg-cyan-500 text-slate-950 px-4 py-2 rounded-2xl hover:bg-cyan-400 transition"
                  >
                    {viewMode === "table" ? "Graph View" : "Table View"}
                  </button>
                </div>

              </div>

              {/* TABLE / GRAPH */}

              <div className="overflow-x-auto mt-8">
                {viewMode === "graph" && (
                  <div className="space-y-6">
                    {graphItems.length === 0 ? (
                      <div className="py-16 text-center text-slate-400">
                        No invoices available for graph view.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {graphItems.map(([vendor, amount], index) => (
                          <div key={vendor} className="bg-slate-950 border border-slate-800 rounded-3xl p-4 shadow-sm">
                            <div className="flex items-center justify-between text-slate-200 mb-2">
                              <span>{vendor}</span>
                              <span className="font-semibold">₹{amount.toLocaleString()}</span>
                            </div>
                            <div className="h-4 rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-cyan-500 transition-all duration-500"
                                style={{ width: Math.max((amount / maxGraphValue) * 100, 4) + '%' }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {viewMode === "table" && (
                  <table className="w-full">

                  <thead>

                    <tr className="border-b border-slate-800 text-slate-400">

                      <th className="text-left py-4">
                        Vendor
                      </th>

                      <th>
                        Invoice #
                      </th>
                     <th>
                      GSTIN
                     </th>
                      <th>
                        Amount
                      </th>

                      <th>
                        Date
                      </th>

                      <th>
                        Status
                      </th>

                      <th>
                        SGST
                      </th>

                      <th>
                        CGST
                      </th>

                      <th>
                        IGST
                      </th>

                      <th>
                        Actions
                      </th>
                     

                    </tr>

                  </thead>

                  <tbody>

                    {displayedInvoices.length === 0 && (

                        <tr>

                          <td
                            colSpan="9"
                            className="text-center py-10 text-slate-500"
                          >

                            No matching invoices found

                          </td>

                        </tr>

                    )}

                    {displayedInvoices.map((invoice) => (

                      <tr
                        key={invoice.id}
                        className="border-b border-slate-800 hover:bg-slate-900 transition-colors"
                      >


                        <td className="py-5">

                          {invoice.vendor}

                        </td>

                        <td className="text-center text-slate-300">

                          {invoice.invoice_number || "-"}

                        </td>

                        <td className="text-center">

                          {invoice.gstin || "-"}

                        </td>

                        <td className="text-center">

                          {formatCurrency(invoice.amount)}

                        </td>

                        <td className="text-center">

                          {invoice.date}

                        </td>

                        <td className="text-center text-green-400">

                          {invoice.status}

                        </td>

                        <td className="text-center">

                          {formatTaxValue(invoice.sgst)}

                        </td>

                        <td className="text-center">

                          {formatTaxValue(invoice.cgst)}

                        </td>

                        <td className="text-center">

                          {formatTaxValue(invoice.igst)}

                        </td>

                        <td className="text-right py-5 space-x-2">
                          <button
                            onClick={() => handleEditInvoice(invoice)}
                            className="bg-slate-700 text-slate-100 px-3 py-2 rounded-xl hover:bg-slate-600 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteInvoice(invoice.id)}
                            className="bg-red-500 text-white px-3 py-2 rounded-xl hover:bg-red-400 transition"
                          >
                            Delete
                          </button>
                        </td>

                      </tr>

                    ))}

                  </tbody>

                </table>
                )}

              </div>

            </div>

          </div>
          )}

        </div>

      </main>

    </div>

  );
}

export default App;