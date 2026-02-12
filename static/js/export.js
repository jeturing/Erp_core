/**
 * Data Export Utilities
 * Exportación de datos a CSV, Excel y PDF
 */

class DataExporter {
    /**
     * Exportar datos a CSV
     * @param {Array} data - Array de objetos a exportar
     * @param {string} filename - Nombre del archivo (sin extensión)
     * @param {Array} columns - Columnas a exportar [{key: 'field', label: 'Header'}]
     */
    static toCSV(data, filename, columns = null) {
        if (!data || data.length === 0) {
            toast.warning('No hay datos para exportar');
            return;
        }

        // Si no se especifican columnas, usar todas las keys del primer objeto
        if (!columns) {
            columns = Object.keys(data[0]).map(key => ({ key, label: key }));
        }

        // Crear header
        const headers = columns.map(col => `"${col.label}"`).join(',');
        
        // Crear filas
        const rows = data.map(item => {
            return columns.map(col => {
                let value = item[col.key];
                
                // Formatear valores especiales
                if (value === null || value === undefined) {
                    value = '';
                } else if (typeof value === 'object') {
                    value = JSON.stringify(value);
                } else if (typeof value === 'string') {
                    // Escapar comillas y manejar saltos de línea
                    value = value.replace(/"/g, '""');
                }
                
                return `"${value}"`;
            }).join(',');
        });

        const csv = [headers, ...rows].join('\n');
        
        // Agregar BOM para Excel
        const bom = '\uFEFF';
        const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
        
        this.downloadBlob(blob, `${filename}.csv`);
        toast.success(`Exportados ${data.length} registros a CSV`);
    }

    /**
     * Exportar datos a JSON
     */
    static toJSON(data, filename) {
        if (!data || data.length === 0) {
            toast.warning('No hay datos para exportar');
            return;
        }

        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
        
        this.downloadBlob(blob, `${filename}.json`);
        toast.success(`Exportados ${data.length} registros a JSON`);
    }

    /**
     * Exportar tabla HTML a CSV
     */
    static tableToCSV(tableSelector, filename) {
        const table = document.querySelector(tableSelector);
        if (!table) {
            toast.error('Tabla no encontrada');
            return;
        }

        const rows = [];
        
        // Headers
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => 
            `"${th.textContent.trim()}"`
        );
        rows.push(headers.join(','));

        // Body rows
        table.querySelectorAll('tbody tr').forEach(tr => {
            const cells = Array.from(tr.querySelectorAll('td')).map(td => {
                let text = td.textContent.trim().replace(/"/g, '""');
                return `"${text}"`;
            });
            rows.push(cells.join(','));
        });

        const csv = rows.join('\n');
        const bom = '\uFEFF';
        const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
        
        this.downloadBlob(blob, `${filename}.csv`);
        toast.success('Tabla exportada a CSV');
    }

    /**
     * Exportar a Excel (XLSX básico usando tabla HTML)
     */
    static toExcel(data, filename, columns = null) {
        if (!data || data.length === 0) {
            toast.warning('No hay datos para exportar');
            return;
        }

        if (!columns) {
            columns = Object.keys(data[0]).map(key => ({ key, label: key }));
        }

        // Crear tabla HTML
        let html = `
            <html xmlns:o="urn:schemas-microsoft-com:office:office" 
                  xmlns:x="urn:schemas-microsoft-com:office:excel">
            <head>
                <meta charset="UTF-8">
                <!--[if gte mso 9]>
                <xml>
                    <x:ExcelWorkbook>
                        <x:ExcelWorksheets>
                            <x:ExcelWorksheet>
                                <x:Name>Datos</x:Name>
                                <x:WorksheetOptions>
                                    <x:DisplayGridlines/>
                                </x:WorksheetOptions>
                            </x:ExcelWorksheet>
                        </x:ExcelWorksheets>
                    </x:ExcelWorkbook>
                </xml>
                <![endif]-->
                <style>
                    table { border-collapse: collapse; }
                    th { background-color: #4F46E5; color: white; font-weight: bold; padding: 8px; border: 1px solid #ddd; }
                    td { padding: 6px; border: 1px solid #ddd; }
                </style>
            </head>
            <body>
                <table>
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col.label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(item => `
                            <tr>
                                ${columns.map(col => `<td>${item[col.key] ?? ''}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </body>
            </html>
        `;

        const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
        this.downloadBlob(blob, `${filename}.xls`);
        toast.success(`Exportados ${data.length} registros a Excel`);
    }

    /**
     * Imprimir datos como tabla
     */
    static print(data, title, columns = null) {
        if (!data || data.length === 0) {
            toast.warning('No hay datos para imprimir');
            return;
        }

        if (!columns) {
            columns = Object.keys(data[0]).map(key => ({ key, label: key }));
        }

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    h1 { font-size: 18px; margin-bottom: 20px; }
                    table { width: 100%; border-collapse: collapse; font-size: 12px; }
                    th { background-color: #4F46E5; color: white; padding: 10px; text-align: left; }
                    td { padding: 8px; border-bottom: 1px solid #ddd; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .footer { margin-top: 20px; font-size: 10px; color: #666; }
                    @media print {
                        body { padding: 0; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                <h1>${title}</h1>
                <table>
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col.label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(item => `
                            <tr>
                                ${columns.map(col => `<td>${item[col.key] ?? '-'}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <p class="footer">
                    Generado: ${new Date().toLocaleString('es-ES')} | 
                    Total: ${data.length} registros
                </p>
                <script>window.print();</script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }

    /**
     * Helper para descargar blob
     */
    static downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

// Funciones globales de conveniencia
window.exportToCSV = (data, filename, columns) => DataExporter.toCSV(data, filename, columns);
window.exportToJSON = (data, filename) => DataExporter.toJSON(data, filename);
window.exportToExcel = (data, filename, columns) => DataExporter.toExcel(data, filename, columns);
window.exportTableToCSV = (tableSelector, filename) => DataExporter.tableToCSV(tableSelector, filename);
window.printData = (data, title, columns) => DataExporter.print(data, title, columns);
