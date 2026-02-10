#!/usr/bin/env node

/**
 * MCP Server for Onboarding System API
 * Provides tools to interact with the FastAPI backend
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";
import fs from "fs/promises";

const API_URL = process.env.API_URL || "http://localhost:4443";
const TOKEN_FILE = process.env.API_TOKEN_FILE || "/opt/onboarding-system/.mcp_token";

let authToken = null;

// Load auth token from file
async function loadToken() {
  try {
    authToken = await fs.readFile(TOKEN_FILE, "utf8");
    authToken = authToken.trim();
  } catch (error) {
    console.error("No auth token found. Run: POST /api/admin/login to get token");
  }
}

// API fetch wrapper
async function apiCall(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(authToken && { Authorization: `Bearer ${authToken}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} - ${JSON.stringify(data)}`);
  }

  return data;
}

// Create MCP server
const server = new Server(
  {
    name: "onboarding-api",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_dashboard_metrics",
        description: "Obtiene métricas del dashboard administrativo (MRR, tenants activos, ingresos)",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "list_tenants",
        description: "Lista todos los tenants con su información de suscripción",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "get_tenant_info",
        description: "Obtiene información detallada de un tenant específico",
        inputSchema: {
          type: "object",
          properties: {
            tenant_id: {
              type: "number",
              description: "ID del tenant",
            },
          },
          required: ["tenant_id"],
        },
      },
      {
        name: "get_tenant_billing",
        description: "Obtiene facturas y método de pago de un tenant",
        inputSchema: {
          type: "object",
          properties: {
            tenant_id: {
              type: "number",
              description: "ID del tenant",
            },
          },
          required: ["tenant_id"],
        },
      },
      {
        name: "admin_login",
        description: "Realiza login como administrador y guarda el token",
        inputSchema: {
          type: "object",
          properties: {
            username: {
              type: "string",
              description: "Username del admin",
            },
            password: {
              type: "string",
              description: "Password del admin",
            },
          },
          required: ["username", "password"],
        },
      },
      {
        name: "health_check",
        description: "Verifica el estado del sistema",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "get_stripe_events",
        description: "Obtiene los eventos de Stripe recientes procesados por el sistema",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "health_check":
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(await apiCall("/health"), null, 2),
            },
          ],
        };

      case "admin_login": {
        const data = await apiCall("/api/login/unified", {
          method: "POST",
          body: JSON.stringify({
            email: args.username,
            password: args.password,
            role: "admin",
          }),
        });

        // Save token
        await fs.writeFile(TOKEN_FILE, data.access_token, "utf8");
        authToken = data.access_token;

        return {
          content: [
            {
              type: "text",
              text: `Login exitoso. Token guardado. Expira en ${data.expires_in} segundos.`,
            },
          ],
        };
      }

      case "get_dashboard_metrics":
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(await apiCall("/api/dashboard/metrics"), null, 2),
            },
          ],
        };

      case "list_tenants":
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(await apiCall("/api/tenants"), null, 2),
            },
          ],
        };

      case "get_tenant_info": {
        // Temporary: use admin endpoint to get customer info
        const tenants = await apiCall("/api/tenants");
        const tenant = tenants.items.find((t) => t.id === args.tenant_id);
        return {
          content: [
            {
              type: "text",
              text: tenant ? JSON.stringify(tenant, null, 2) : "Tenant not found",
            },
          ],
        };
      }

      case "get_tenant_billing": {
        // Note: This would require tenant auth token in production
        return {
          content: [
            {
              type: "text",
              text: "Billing endpoint requires tenant authentication. Use tenant login first.",
            },
          ],
        };
      }

      case "get_stripe_events":
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(await apiCall("/api/admin/stripe-events"), null, 2),
            },
          ],
        };

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  await loadToken();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Onboarding API MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
