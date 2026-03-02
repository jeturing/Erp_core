# Full-Stack Consistency Guardian

Este skill asegura que el código frontend esté perfectamente sincronizado con el backend, evitando los problemas más comunes de desalineación en desarrollo con IA.

---

## ¿Cuándo usar este skill?
- Cuando desarrolles un nuevo endpoint de API y su consumidor frontend
- Cuando la IA genere componentes que consumen APIs
- Cuando necesites asegurar que los estados (loading, error, success) estén completos
- Cuando trabajes con FastAPI + React/Svelte/React Native
- Cuando trabajes con modelos de Odoo y necesites interfaces consistentes
- Cuando actualices un endpoint y necesites actualizar todos los consumidores

---

## Problema que resuelve
El problema típico: La IA genera código backend que funciona bien, pero el frontend:
- No maneja correctamente los estados de carga y error
- Espera estructuras de datos diferentes a las que devuelve la API
- Envía datos en formato incorrecto
- No valida los datos de la misma forma que el backend

**La solución:** Este skill actúa como guardián de consistencia, asegurando que:
- Los tipos de datos coincidan exactamente
- Los estados sean completos y robustos
- Las validaciones sean consistentes
- El código sea predecible y mantenible

---

## Principios fundamentales

### 1. Contrato de datos primero
Antes de escribir cualquier código, identifica o define el contrato de datos:
- ¿Qué modelos Pydantic están involucrados?
- ¿Qué modelos de Odoo se usan?
- ¿Cuál es la estructura exacta de request/response?

### 2. Estados completos siempre
TODO código que consuma una API DEBE manejar estos estados:
- idle: Estado inicial antes de cualquier acción
- loading: Mientras se espera la respuesta
- success: Cuando se recibió respuesta exitosa (con los datos)
- error: Cuando falló (con mensaje de error detallado)

NUNCA asumas que solo necesitas "loading" y "data". SIEMPRE implementa los 4 estados.

### 3. Validación bidireccional
- El frontend debe validar ANTES de enviar (mismo criterio que el backend)
- El frontend debe validar DESPUÉS de recibir (type safety)
- Usa los mismos mensajes de error en ambos lados

### 4. Tipos TypeScript desde Python
Cuando sea posible, genera tipos TypeScript automáticamente desde:
- Modelos Pydantic (FastAPI)
- Modelos Odoo (fields)
- Respuestas de API documentadas

---

## Workflow de implementación

### Paso 1: Analizar el contrato backend
Si el usuario proporciona un modelo Pydantic o Odoo:

```python
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: str
    is_active: bool
```

Tu trabajo:
- Identifica todos los campos y sus tipos
- Identifica campos requeridos vs opcionales
- Identifica validaciones (email, min/max length, etc.)
- Anota los posibles errores que puede devolver el endpoint

### Paso 2: Generar tipos TypeScript
Convierte el modelo a TypeScript exacto:

```typescript
// Generado desde UserCreate
interface UserCreateData {
  username: string;
  email: string;
  full_name?: string;
}

// Generado desde UserResponse
interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  created_at: string;
  is_active: boolean;
}

// Estados de la operación
interface UserState {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: User | null;
  error: string | null;
}
```

### Paso 3: Generar código frontend consistente

#### Para React (con hooks):
```typescript
import { useState } from 'react';

interface UseUserCreateReturn {
  createUser: (data: UserCreateData) => Promise<void>;
  state: UserState;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
}

export function useUserCreate(): UseUserCreateReturn {
  const [state, setState] = useState<UserState>({
    status: 'idle',
    data: null,
    error: null,
  });

  const createUser = async (data: UserCreateData) => {
    setState({ status: 'loading', data: null, error: null });
    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error creating user');
      }
      const user: User = await response.json();
      setState({ status: 'success', data: user, error: null });
    } catch (error) {
      setState({
        status: 'error',
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  return {
    createUser,
    state,
    isLoading: state.status === 'loading',
    isError: state.status === 'error',
    isSuccess: state.status === 'success',
  };
}
```

#### Para Svelte (con stores):
```typescript
import { writable, derived } from 'svelte/store';

interface UserStore extends UserState {
  createUser: (data: UserCreateData) => Promise<void>;
}

function createUserStore() {
  const { subscribe, set, update } = writable<UserState>({
    status: 'idle',
    data: null,
    error: null,
  });

  return {
    subscribe,
    createUser: async (data: UserCreateData) => {
      set({ status: 'loading', data: null, error: null });
      try {
        const response = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error creating user');
        }
        const user: User = await response.json();
        set({ status: 'success', data: user, error: null });
      } catch (error) {
        set({
          status: 'error',
          data: null,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    },
    reset: () => set({ status: 'idle', data: null, error: null }),
  };
}

export const userStore = createUserStore();

// Derived stores para conveniencia
export const isLoading = derived(userStore, $store => $store.status === 'loading');
export const isError = derived(userStore, $store => $store.status === 'error');
export const isSuccess = derived(userStore, $store => $store.status === 'success');
```

#### Para React Native / Expo:
(Similar a React, pero usando fetch con URL absoluta y manejo de tokens)

---

## Checklist de validación

### Backend checklist:
- El endpoint está definido claramente (URL, método, auth)
- Los modelos Pydantic/Odoo están identificados
- Las validaciones están documentadas
- Los posibles errores están identificados
- Los status codes están claros

### Frontend checklist:
- Tipos TypeScript generados desde el backend
- Estados completos: idle, loading, success, error
- Validación client-side coincide con server-side
- Manejo de errores con mensajes claros
- UI muestra feedback para todos los estados
- Loading states desabilitan inputs
- Errores se muestran al usuario
- Success states confirman la acción

### Consistencia checklist:
- Los nombres de campos son idénticos (camelCase vs snake_case manejado)
- Los tipos de datos coinciden exactamente
- Las validaciones son las mismas
- Los mensajes de error son consistentes
- La estructura de datos anidados coincide

---

## Casos comunes y patrones

### Listas paginadas
```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface UsersListState {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: PaginatedResponse<User> | null;
  error: string | null;
}
```

### Formularios con validación
```typescript
interface FormErrors {
  [key: string]: string[];
}

interface FormState<T> {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: T | null;
  errors: FormErrors | null;
  fieldErrors: FormErrors;
}
```

### Autenticación y tokens
```typescript
interface AuthState {
  status: 'idle' | 'loading' | 'success' | 'error';
  token: string | null;
  user: User | null;
  error: string | null;
}
```

### Optimistic updates
```typescript
const deleteUser = async (userId: number) => {
  setState({ status: 'loading', data: state.data?.filter(u => u.id !== userId) ?? null, error: null });
  try {
    await fetch(`/api/users/${userId}`, { method: 'DELETE' });
    setState({ status: 'success', data: state.data, error: null });
  } catch (error) {
    const originalData = await refetchUsers();
    setState({ status: 'error', data: originalData, error: 'Failed to delete user' });
  }
};
```

---

## Convenciones de nombres
- Backend (Python/Odoo): snake_case para variables y funciones, PascalCase para clases y modelos, endpoints en snake_case
- Frontend (TypeScript): camelCase para variables y funciones, PascalCase para componentes, interfaces, tipos
- Convertir automáticamente entre snake_case y camelCase cuando sea necesario

---

## Instrucciones finales
Cuando uses este skill:
- Lee primero el contrato: Identifica modelos, endpoints, tipos
- Genera tipos TypeScript: Desde Pydantic/Odoo models
- Implementa estados completos: idle, loading, success, error
- Crea hooks/stores: Encapsula la lógica de API
- Genera componentes: Con UI para todos los estados
- Valida consistencia: Revisa el checklist completo

El resultado debe ser código que:
- Funcione a la primera sin ajustes manuales
- Maneje todos los casos edge (errores, loading, vacío)
- Sea type-safe de extremo a extremo
- Sea predecible y fácil de mantener
- Siga las convenciones del proyecto

---

## Plantilla rápida
1. ¿Qué endpoint del backend se va a usar/crear?
2. ¿Qué modelo Pydantic/Odoo está involucrado?
3. ¿Es para React, Svelte, o móvil?

Genera en este orden:
- Tipos TypeScript
- Hook/Store con estados completos
- Componente con UI para todos los estados
- Tests básicos (opcional)

Valida antes de entregar:
- Revisa el checklist completo
- Confirma que todos los estados están manejados
- Verifica que los tipos coincidan exactamente

---

Recuerda: El objetivo es que el código generado sea tan consistente que NUNCA requiera ajustes manuales para alinear backend y frontend. Si algo falla, es un bug del skill, no del usuario.
