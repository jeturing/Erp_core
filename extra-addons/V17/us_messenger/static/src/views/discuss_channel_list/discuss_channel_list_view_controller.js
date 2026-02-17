/* @odoo-module */

import { useState } from "@odoo/owl";

import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class DiscussChannelListController extends ListController {
    setup() {
        super.setup(...arguments);
        this.threadService = useService("mail.thread");
        this.store = useState(useService("mail.store"));
        this.ui = useState(useService("ui"));
    }

    async openRecord(record) {
        let thread = this.store.Thread.get({
            model: "discuss.channel",
            id: record.data.channel_id[0],
        });
        if (!thread?.type) {
            thread = await this.threadService.fetchChannel(record.data.channel_id[0]);
        }
        if (thread) {
            this.threadService.pin(thread);
            return this.threadService.open(thread);
        } else {
            this.env.services.notification.add(_t("Join the channel to view the communication history"),{
                        type: 'warning',
                    });
                    return;
        }

        return super.openRecord(record);
    }
}
