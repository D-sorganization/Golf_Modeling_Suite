function out = validate_3d_fullbody(model_name, opts)
%VALIDATE_3D_FULLBODY  Sanity-check the built 3D_FullBody model.
%
%   OUT = VALIDATE_3D_FULLBODY(MODEL_NAME, OPTS) runs three checks:
%
%     1. Block count: total + nonvirtual estimate vs. the Home-license
%        1000-block budget.
%     2. Signal count: how many channels are exposed by
%        CombinedSignalBus / SignalLogging after the prune phase.
%     3. Smoke simulation: load + sim for ``opts.smoke_time`` seconds
%        with default inputs.  Flags any solver / unconnected-port
%        errors.
%
%   Args:
%       MODEL_NAME (char/string)  loaded Simulink model name.
%       OPTS (struct)
%         .verbose       default true.
%         .smoke_time    default 0.005 s.
%         .budget        default 1000 (Home license).
%
%   Returns:
%       OUT (struct)
%         .passed                bool — all three checks passed.
%         .total_blocks          int.
%         .nonvirtual_estimate   int — based on BlockType heuristics.
%         .within_budget         bool.
%         .logged_signals        int — Outport blocks at top level
%                                approximating CombinedSignalBus channels.
%         .smoke_sim_status      "success" | "warning" | "failed" | "skipped".
%         .smoke_sim_message     string (last error message if failed).
%
%   See also: BUILD_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose');    opts.verbose    = true;  end
    if ~isfield(opts, 'smoke_time'); opts.smoke_time = 0.005; end
    if ~isfield(opts, 'budget');     opts.budget     = 1000;  end

    if ~bdIsLoaded(char(model_name))
        error('validate_3d_fullbody:notLoaded', ...
              'Model %s is not loaded.', model_name);
    end

    out = struct( ...
        'passed',              false, ...
        'total_blocks',        0, ...
        'nonvirtual_estimate', 0, ...
        'within_budget',       false, ...
        'logged_signals',      0, ...
        'smoke_sim_status',    "skipped", ...
        'smoke_sim_message',   "");

    % --- Check 1: block count ---------------------------------------
    blocks = find_system(char(model_name), ...
        'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Type', 'block');
    out.total_blocks = numel(blocks);

    nonvirtual_count = 0;
    virtual_types = {'SubSystem', 'Mux', 'Demux', 'Inport', 'Outport', ...
                     'BusCreator', 'BusSelector', 'Goto', 'From', ...
                     'GotoTagVisibility', 'Terminator', 'Ground', ...
                     'EnablePort', 'TriggerPort', 'ActionPort'};
    for k = 1:numel(blocks)
        try
            bt = get_param(blocks{k}, 'BlockType');
        catch
            continue
        end
        if ~any(strcmp(bt, virtual_types))
            nonvirtual_count = nonvirtual_count + 1;
        end
    end
    out.nonvirtual_estimate = nonvirtual_count;
    out.within_budget = nonvirtual_count <= opts.budget;

    if opts.verbose
        fprintf('validate_3d_fullbody:\n');
        fprintf('  total_blocks         = %d\n', out.total_blocks);
        fprintf('  nonvirtual_estimate  = %d  (budget %d)  -> %s\n', ...
            out.nonvirtual_estimate, opts.budget, ...
            ternary(out.within_budget, 'WITHIN', 'OVER'));
    end

    % --- Check 2: logged signal count -------------------------------
    % Count top-level Outport blocks (proxy for CombinedSignalBus
    % subfields after the bus is created internally).
    try
        top_outports = find_system(char(model_name), ...
            'SearchDepth', 1, 'BlockType', 'Outport');
        out.logged_signals = numel(top_outports);
    catch
        out.logged_signals = 0;
    end
    if opts.verbose
        fprintf('  logged_signals       = %d\n', out.logged_signals);
    end

    % --- Check 3: smoke simulation ----------------------------------
    if opts.smoke_time <= 0
        out.smoke_sim_status = "skipped";
        if opts.verbose
            fprintf('  smoke_sim            = skipped (smoke_time <= 0)\n');
        end
    else
        try
            simIn = Simulink.SimulationInput(char(model_name));
            simIn = simIn.setModelParameter('StopTime', ...
                num2str(double(opts.smoke_time)));
            simIn = simIn.setModelParameter('FastRestart', 'off');
            simOut = sim(simIn);
            if isprop(simOut, 'ErrorMessage') && ~isempty(simOut.ErrorMessage)
                out.smoke_sim_status  = "failed";
                out.smoke_sim_message = string(simOut.ErrorMessage);
            elseif isprop(simOut, 'SimulationMetadata')
                md = simOut.SimulationMetadata;
                if isfield(md, 'ExecutionInfo') && isfield(md.ExecutionInfo, 'StopEvent')
                    se = string(md.ExecutionInfo.StopEvent);
                    if ismember(se, ["ReachedStopTime", "CompletedNormally", ...
                                     "SimulationStopped", "ExternalInputStopped"])
                        out.smoke_sim_status = "success";
                    else
                        out.smoke_sim_status = "warning";
                        out.smoke_sim_message = se;
                    end
                else
                    out.smoke_sim_status = "warning";
                    out.smoke_sim_message = "no SimulationMetadata.ExecutionInfo";
                end
            else
                out.smoke_sim_status = "warning";
                out.smoke_sim_message = "no SimulationMetadata";
            end
        catch ME
            out.smoke_sim_status  = "failed";
            out.smoke_sim_message = string(ME.message);
        end
        if opts.verbose
            fprintf('  smoke_sim            = %s\n', out.smoke_sim_status);
            if strlength(out.smoke_sim_message) > 0
                fprintf('     message: %s\n', out.smoke_sim_message);
            end
        end
    end

    out.passed = out.within_budget && ...
                 (out.smoke_sim_status == "success" || ...
                  out.smoke_sim_status == "skipped");
    if opts.verbose
        fprintf('  passed               = %s\n', ternary(out.passed, 'true', 'false'));
    end
end


function out = ternary(cond, a, b)
    if cond; out = a; else; out = b; end
end
