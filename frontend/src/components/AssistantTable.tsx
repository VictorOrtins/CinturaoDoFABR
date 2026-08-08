import type { AssistantTable as AssistantTableData } from "../api/types";
import "./AssistantTable.css";

interface AssistantTableProps {
  table: AssistantTableData;
}

export function AssistantTable({ table }: AssistantTableProps) {
  return (
    <div className="assistant-table__wrap">
      <table className="assistant-table">
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, index) => (
            <tr key={index}>
              {table.columns.map((column) => (
                <td key={column}>{row[column]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
