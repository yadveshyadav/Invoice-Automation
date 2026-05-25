import {
  FaChartPie,
  FaUpload,
  FaFileInvoice,
  FaTable,
  FaChevronLeft,
  FaChevronRight
} from "react-icons/fa";
import { useState } from "react";

function Sidebar({

  activePage,
  setActivePage

}) {

  const menuItems = [

    {
      id: "dashboard",
      title: "Dashboard",
      icon: <FaChartPie />
    },

    {
      id: "upload",
      title: "Upload",
      icon: <FaUpload />
    },

    {
      id: "invoices",
      title: "Invoices",
      icon: <FaFileInvoice />
    },

    {
      id: "tables",
      title: "Tables",
      icon: <FaTable />
    }

  ];

  const [collapsed, setCollapsed] = useState(false);

  return (

    <div className={`sidebar-responsive ${collapsed ? "collapsed w-20 md:w-20 p-3" : "w-40 md:w-64 p-5"} bg-slate-900 min-h-screen md:min-h-screen border-b md:border-b-0 md:border-r border-slate-800 transition-all duration-300 relative overflow-hidden`}>

      <div className={`flex items-center justify-between ${collapsed ? "mb-4" : "mb-6"}`}>

        <h1 className={`sidebar-title ${collapsed ? "text-xl" : "text-3xl"} font-bold text-cyan-400 truncate`}> 

          {collapsed ? "IA" : "InvoiceAI"}

        </h1>

        <button
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={`${collapsed ? "p-1" : "p-2"} rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300`}
        >
          {collapsed ? <FaChevronRight /> : <FaChevronLeft />}
        </button>

      </div>

      <ul className="space-y-4">

        {menuItems.map((item) => (

          <li
            key={item.id}

            onClick={() =>
              setActivePage(item.id)
            }

            className={`

              p-4
              rounded-xl
              flex
              ${collapsed ? "justify-center gap-0" : "items-center gap-3"}
              cursor-pointer
              transition-all
              duration-300

              ${
                activePage === item.id

                  ? "bg-cyan-500 text-slate-950 shadow-lg"

                  : "hover:bg-slate-800 text-white"
              }

            `}
          >

            {item.icon}

            {!collapsed && (
              <span className="sidebar-label">
                {item.title}
              </span>
            )}

          </li>

        ))}

      </ul>

    </div>

  );
}

export default Sidebar;