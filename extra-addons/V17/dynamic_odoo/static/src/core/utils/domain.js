/** @odoo-module **/
const py = window.py;

export const domainToCondition = (domain) => {
    if (!domain.length) {
        return 'True';
    }

    function consume(stack) {
        let len = stack.length;
        if (len <= 1) {
            return stack;
        } else if (stack[len - 1] === '|' || stack[len - 1] === '&' || stack[len - 2] === '|' || stack[len - 2] === '&') {
            return stack;
        } else if (len == 2) {
            stack.splice(-2, 2, stack[len - 2] + ' and ' + stack[len - 1]);
        } else if (stack[len - 3] == '|') {
            if (len === 3) {
                stack.splice(-3, 3, stack[len - 2] + ' or ' + stack[len - 1]);
            } else {
                stack.splice(-3, 3, '(' + stack[len - 2] + ' or ' + stack[len - 1] + ')');
            }
        } else {
            stack.splice(-3, 3, stack[len - 2] + ' and ' + stack[len - 1]);
        }
        consume(stack);
    }

    let stack = [];
    _.each(domain, function (dom) {
        if (dom === '|' || dom === '&') {
            stack.push(dom);
        } else {
            let operator = dom[1] === '=' ? '==' : dom[1];
            if (!operator) {
                throw new Error('Wrong operator for this domain');
            }
            if (operator === '!=' && dom[2] === false) { // the field is set
                stack.push(dom[0]);
            } else if (dom[2] === null || dom[2] === true || dom[2] === false) {
                stack.push(dom[0] + ' ' + (operator === '!=' ? 'is not ' : 'is ') + (dom[2] === null ? 'None' : (dom[2] ? 'True' : 'False')));
            } else {
                stack.push(dom[0] + ' ' + operator + ' ' + JSON.stringify(dom[2]));
            }
            consume(stack);
        }
    });

    if (stack.length !== 1) {
        throw new Error('Wrong domain');
    }

    return stack[0];
}

export const conditionToDomain = (condition) => {
    if (!condition || condition.match(/^\s*(True)?\s*$/)) {
        return [];
    }
    let ast = py.parse(py.tokenize(condition));

    const astToStackValue = (node) => {
        const nodeId = node.id;
        switch (nodeId) {
            case '(name)':
                return node.value;
            case '.':
                return astToStackValue(node.first) + '.' + astToStackValue(node.second);
            case '(string)':
                return node.value;
            case '(number)':
                return node.value;
            case '(constant)':
                return node.value === 'None' ? null : node.value === 'True' ? true : false;
            case '(':
            case '[':
                return _.map(node.first, function (node) {
                    return astToStackValue(node);
                });
        }
    }
    const astToStack = (node) => {
        switch (node.id) {
            case '(name)':
                return [[astToStackValue(node), '!=', false]];
            case '.':
                return [[astToStackValue(node.first) + '.' + astToStackValue(node.second), '!=', false]];
            case 'not':
                return [[astToStackValue(node.first), '=', false]];

            case 'or':
                return ['|'].concat(astToStack(node.first)).concat(astToStack(node.second));
            case 'and':
                return ['&'].concat(astToStack(node.first)).concat(astToStack(node.second));
            case '(comparator)':
                if (node.operators.length !== 1) {
                    throw new Error('Wrong condition to convert in domain');
                }
                let right = astToStackValue(node.expressions[0]),
                    left = astToStackValue(node.expressions[1]),
                    operator = node.operators[0];
                switch (operator) {
                    case 'is':
                        operator = '=';
                        break;
                    case 'is not':
                        operator = '!=';
                        break;
                    case '==':
                        operator = '=';
                        break;
                }
                return [[right, operator, left]];
            default:
                throw "Condition cannot be transformed into domain";
        }
    }

    return astToStack(ast);
}