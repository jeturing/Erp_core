/**
 * Meta Pixel Events Helper
 * Rastrear eventos estándar y personalizados para Meta
 */

declare global {
  interface Window {
    fbq?: (action: string, event: string, data?: Record<string, any>) => void;
  }
}

export const metaEvents = {
  /**
   * ViewContent - Usuario vio contenido (banco de preguntas)
   */
  viewContent: (bankSlug: string, bankName: string, price: number) => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'ViewContent', {
        content_ids: [bankSlug],
        content_name: bankName,
        content_type: 'product',
        value: price,
        currency: 'USD',
      });
    }
  },

  /**
   * InitiateCheckout - Usuario inició proceso de compra
   */
  initiateCheckout: (bankSlug: string, bankName: string, price: number, email?: string) => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'InitiateCheckout', {
        content_ids: [bankSlug],
        content_name: bankName,
        content_type: 'product',
        value: price,
        currency: 'USD',
        email: email,
      });
    }
  },

  /**
   * Purchase - Compra completada
   */
  purchase: (sessionId: string, bankSlug: string, bankName: string, amount: number) => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'Purchase', {
        content_ids: [bankSlug],
        content_name: bankName,
        content_type: 'product',
        value: amount,
        currency: 'USD',
        transaction_id: sessionId,
      });
    }
  },

  /**
   * StartTrial - Usuario inició prueba gratuita
   */
  startTrial: (bankSlug: string, bankName: string) => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'StartTrial', {
        content_ids: [bankSlug],
        content_name: bankName,
        content_type: 'product',
      });
    }
  },

  /**
   * Search - Usuario realizó búsqueda
   */
  search: (query: string) => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'Search', {
        search_string: query,
      });
    }
  },

  /**
   * Contact - Usuario contactó (chat, email, etc)
   */
  contact: () => {
    if (typeof window !== 'undefined' && window.fbq) {
      window.fbq('track', 'Contact');
    }
  },
};
