function ml_workflow_gui()
%ML_WORKFLOW_GUI Lightweight UI for the golf ML club-control workflow.

thisFile = mfilename('fullpath');
mlDir = fileparts(fileparts(thisFile));
dataDir = fullfile(mlDir, 'data', 'processed');

fig = uifigure('Name', 'Golf ML Club Control', 'Position', [100 100 820 560]);
grid = uigridlayout(fig, [10 4]);
grid.RowHeight = {30, 30, 30, 30, 30, 30, 30, 30, '1x', 30};
grid.ColumnWidth = {150, '1x', 130, 130};

uilabel(grid, 'Text', 'Scenario');
scenarioDropDown = uidropdown(grid, ...
    'Items', {'full-swing', 'downswing'}, ...
    'Value', 'downswing');
scenarioDropDown.Layout.Column = [2 4];

uilabel(grid, 'Text', 'Python');
pythonField = uieditfield(grid, 'text', 'Value', 'py -3.12');
pythonField.Layout.Column = [2 4];

uilabel(grid, 'Text', 'Target CSV');
targetField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'TW_ProV1_club_target.csv'));
targetField.Layout.Column = 2;
uibutton(grid, 'Text', 'Prepare', 'ButtonPushedFcn', @(~, ~) runPrepareTarget());
uibutton(grid, 'Text', 'Slice', 'ButtonPushedFcn', @(~, ~) runSliceTarget());

uilabel(grid, 'Text', 'Sim CSV');
simField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'simulated_club_motion.csv'));
simField.Layout.Column = 2;
uibutton(grid, 'Text', 'Calibrate', 'ButtonPushedFcn', @(~, ~) runCalibrateTarget());
uibutton(grid, 'Text', 'Compare', 'ButtonPushedFcn', @(~, ~) runCompareMotion());

uilabel(grid, 'Text', 'Start MAT');
startField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'ml_downswing_start_state.mat'));
startField.Layout.Column = 2;
uibutton(grid, 'Text', 'Export Start', 'ButtonPushedFcn', @(~, ~) runExportStart());
uibutton(grid, 'Text', 'Run Model', 'ButtonPushedFcn', @(~, ~) runModel());

uilabel(grid, 'Text', 'Torque CSV');
torqueField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'optimized_club_torques.csv'));
torqueField.Layout.Column = 2;
uibutton(grid, 'Text', 'Optimize Tau', 'ButtonPushedFcn', @(~, ~) runOptimizeTorque());
uibutton(grid, 'Text', 'Export Poly', 'ButtonPushedFcn', @(~, ~) runExportPolynomial());

uilabel(grid, 'Text', 'Polynomial MAT');
polyField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'ml_torque_polynomial_inputs.mat'));
polyField.Layout.Column = [2 4];

uilabel(grid, 'Text', 'Reference Body CSV');
referenceField = uieditfield(grid, 'text', ...
    'Value', fullfile(dataDir, 'reference_body_state.csv'));
referenceField.Layout.Column = [2 4];

logArea = uitextarea(grid, 'Editable', 'off');
logArea.Layout.Row = 9;
logArea.Layout.Column = [1 4];

uibutton(grid, 'Text', 'Open ML Folder', 'ButtonPushedFcn', @(~, ~) winopen(mlDir));
uibutton(grid, 'Text', 'Clear Log', 'ButtonPushedFcn', @(~, ~) set(logArea, 'Value', {}));

    function runPrepareTarget()
        command = sprintf('%s "%s" --output "%s"', ...
            pythonField.Value, fullfile(mlDir, 'prepare_club_target_trajectory.py'), targetField.Value);
        runCommand(command);
    end

    function runSliceTarget()
        slicedCsv = scenarioPath('club_target_sliced.csv');
        command = sprintf('%s "%s" --input-csv "%s" --output-csv "%s" --scenario %s --reset-time', ...
            pythonField.Value, fullfile(mlDir, 'slice_club_target.py'), targetField.Value, slicedCsv, scenarioDropDown.Value);
        runCommand(command);
        targetField.Value = slicedCsv;
        startField.Value = scenarioPath('start_state.mat');
    end

    function runCalibrateTarget()
        calibratedCsv = scenarioPath('club_target_calibrated.csv');
        calibrationJson = scenarioPath('club_target_calibration.json');
        command = sprintf('%s "%s" --target-csv "%s" --sim-csv "%s" --output-csv "%s" --output-json "%s"', ...
            pythonField.Value, fullfile(mlDir, 'calibrate_club_target_to_sim.py'), targetField.Value, simField.Value, calibratedCsv, calibrationJson);
        runCommand(command);
        targetField.Value = calibratedCsv;
    end

    function runExportStart()
        export_start_state_from_input_file(scenarioDropDown.Value, startField.Value);
        appendLog(sprintf('Exported %s', startField.Value));
    end

    function runOptimizeTorque()
        checkpoint = fullfile(mlDir, 'runs', 'club_direct_10_cpu', 'best_model.pt');
        command = sprintf('%s "%s" --checkpoint "%s" --desired-club-csv "%s" --reference-body-csv "%s" --output-csv "%s"', ...
            pythonField.Value, fullfile(mlDir, 'optimize_torque_sequence_for_club.py'), checkpoint, targetField.Value, referenceField.Value, torqueField.Value);
        runCommand(command);
    end

    function runExportPolynomial()
        command = sprintf('%s "%s" --torque-csv "%s" --output-mat "%s"', ...
            pythonField.Value, fullfile(mlDir, 'export_torque_polynomials.py'), torqueField.Value, polyField.Value);
        runCommand(command);
    end

    function runModel()
        simOut = run_ml_polynomial_input_swing(polyField.Value, 'GolfSwing3D_Kinetic', startField.Value);
        assignin('base', 'mlWorkflowSimOut', simOut);
        export_simulated_club_csv(simOut, simField.Value);
        appendLog(sprintf('Ran model and exported %s', simField.Value));
    end

    function runCompareMotion()
        outputJson = scenarioPath('club_motion_comparison.json');
        outputPng = scenarioPath('club_motion_comparison.png');
        command = sprintf('%s "%s" --target-csv "%s" --sim-csv "%s" --output-json "%s" --output-png "%s"', ...
            pythonField.Value, fullfile(mlDir, 'compare_simulated_club_motion.py'), targetField.Value, simField.Value, outputJson, outputPng);
        runCommand(command);
    end

    function outputPath = scenarioPath(fileName)
        outputPath = fullfile(dataDir, sprintf('%s_%s', scenarioDropDown.Value, fileName));
    end

    function runCommand(command)
        appendLog(command);
        [status, output] = system(command);
        appendLog(output);
        if status ~= 0
            appendLog(sprintf('Command failed with status %d', status));
        end
    end

    function appendLog(message)
        current = logArea.Value;
        if ischar(current)
            current = {current};
        end
        lines = splitlines(string(message));
        logArea.Value = [current; cellstr(lines(:))];
        drawnow;
    end
end
