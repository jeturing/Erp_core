/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { Domain } from "@web/core/domain";
import { OMMItem } from "@odoo_menu_management/components/menu_item/menu_item";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onWillUpdateProps, useState } = owl;


export class MenuUi extends Component {
    static template = "odoo_menu_management.MenuUi";
    static components = { OMMItem };
    static props = { ... standardActionServiceProps };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({
            helps: null,
            menus: null,
            searchbarInputs: [],
            searchIn: "name",
            filterInputs: [],
            filerIn: "all",
        });
        this.orm = useService("orm");
        this.searchDomain = [];
        this.filtersDomain = [];
        this.filterName = _lt("All");
        onWillStart(async () => {
            const proms = [
                this._onLoadMenus(this.props),
                this._onLoadHelps(this.props),
                this._onLoadSearch(),
                this._onLoadFilters(),
            ]
            return Promise.all(proms);
        });
        onWillUpdateProps(async (nextProps) => {
            await this._onLoadMenus(nextProps);
        });
    }
    /*
    * The method to get help notes for the columns
    */
    async _onLoadHelps(props) {
        const helpNotes = await this.orm.call("ir.ui.menu", "action_get_helps", []);
        Object.assign(this.state, { helps: helpNotes });
    }
    /*
    * The method to get the current menus
    */
    async _onLoadMenus(props) {
        const targetDomain = await this._getFullDomain();
        const irMenus = await this.orm.call("ir.ui.menu", "action_get_menu_hierarchy", [targetDomain]);
        Object.assign(this.state, { menus: irMenus });
    }
    /*
    * The method to prepare filters and search domain
    */
    async _getFullDomain() {
        return Domain.and([this.searchDomain, this.filtersDomain]).toList();
    }
    /*
    * The method to prepare all available search options
    */
    async _onLoadSearch() {
        Object.assign(this.state, {
            searchbarInputs: [
                { id: "name", name: _lt("Menu Title") },
                { id: "parent_id", name: _lt("Parent Menu") },
                { id: "hide_user_global_ids", name: _lt("Hide for users (global)") },
                { id: "hide_user_ids", name: _lt("Hide for users (personal)") },
                { id: "show_user_ids", name: _lt("Show only for users") },
                { id: "hide_for_company_ids", name: _lt("Hide for companies") },
                { id: "show_for_company_ids", name: _lt("Show only for companies") },
                { id: "show_for_group_ids", name: _lt("Show only for groups") },
            ]
        });
    }
    /*
    * The method to prepare all available filters
    */
    async _onLoadFilters() {
        Object.assign(this.state, {
            filterInputs: [
                { id: "all", name: _lt("All"), domain: [] },
                { id: "root", name: _lt("Only root"), domain: [["parent_id", "=", false]] },
                { id: "everyone_hidden", name: _lt("Hidden for everyone"), domain: [["hide_global", "=", true]] },
                { id: "everyone_not_hidden", name: _lt("Not hidden for everyone"), domain: [["hide_global", "=", false]] },
                { id: "archived", name: _lt("Archived"), domain: [["active", "=", false]] },
            ]
        });
    }
    /*
    * The method to select the search criteria
    */
    async _onSelectSearch(searchId) {
        Object.assign(this.state, { searchIn: searchId });
        if (this.state.searchInput) {
            await this._onExecuteSearch();
        }
    }
    /*
    * The method to execute search
    */
    async _onExecuteSearch() {
        const searchInput = $("#omm_search_input");
        if (!searchInput.length || !searchInput[0].value || searchInput[0].value == "") {
            this.state.searchInput = false;
            this.searchDomain = []
        }
        else {
            this.state.searchInput = searchInput[0].value;
            this.searchDomain = [[this.state.searchIn, "ilike", this.state.searchInput]];
        };
        await this._onLoadMenus(this.props);
    }
    /*
    * The method to manage keyup on search input > if enter then make search
    */
    async _onSearchkeyUp(event) {
        if (event.keyCode === 13) {
            await this._onExecuteSearch();
        };
    }
    /*
    * The method to select the search criteria
    */
    async _onSelectFilter(filterId, filterName, filterDomain) {
        Object.assign(this.state, { filerIn: filterId });
        this.filterName = filterName;
        this.filtersDomain = filterDomain;
        await this._onLoadMenus(this.props);
    }
    /*
    * The method to clear search
    */
    async _onClearSearch() {
        const searchInput = $("#omm_search_input");
        if (searchInput.length) { searchInput[0].value = "" };
        Object.assign(this.state, { filerIn: "all" });
        this.filterName = _lt("All");
        this.filtersDomain = [];
        await this._onExecuteSearch();
    }
};

registry.category("actions").add("odoo.menu.management", MenuUi);
