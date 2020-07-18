def varDeg(*args):
    if len(args)<2:
        return "wrong input. Not enough arguments"
    varNames = args[0]
    varTraces = args[1:]
    if len(varNames) != len(varTraces):
        return "wrong input. Traces and variable names don't match"
    traceLength = len(varTraces[0])
    coeffs = dict()
    for i in range(len(varNames)-1):
        for j in range(i+1, len(varNames)):
            valueList = dividedDiff(varTraces[i], varTraces[j])
            if valueList != None and valueList[len(valueList)-1] == 0:
                coeffs[(varNames[i], varNames[j])] = valueList
            else:
                valueList = dividedDiff(varTraces[j], varTraces[i])
                if valueList != None and valueList[len(valueList)-1] == 0:
                    coeffs[varNames[j], varNames[i]] = valueList

    print(coeffs)
    for tuple in coeffs:
        coeffList = coeffs[tuple]
        depVar = tuple[1]
        indepVar = tuple[0]
        indepVarList = varTraces[varNames.index(indepVar)]
        eqn = depVar + ' = '
        lastTerm = ''
        for i in range(len(coeffList)):
            if i>=1:
                lastTerm = lastTerm + '('+indepVar + ' - ' + str(indepVarList[i-1])+')'
            if i == 0:
                eqn += str(coeffList[i])
            else:
                eqn += '+('+str(coeffList[i])+')*'+lastTerm
        print(eqn)




def dividedDiff(trace1, trace2):
    if trace2 == []:
        return None
    list1 = trace1.copy()
    list2 = trace2.copy()
    tempList = []
    coeffs = [list2[0]]
    diff = 1
    size = len(list2)
    while size>1:
        for i in range(len(list2)-1):
            tempList.append( (list2[i+1]-list2[i])/(list1[i+diff]-list1[i]))
        coeffs.append(tempList[0])
        size = len(tempList)
        list2 = tempList.copy()
        tempList = []
        diff += 1
    return coeffs

#Duplicate check later
