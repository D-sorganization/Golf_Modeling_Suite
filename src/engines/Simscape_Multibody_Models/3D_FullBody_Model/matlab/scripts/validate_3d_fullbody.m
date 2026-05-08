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
%         .report_path   optional JSON validation report path.
%         .source_model_path optional source model path for reporting.
%         .target_model_path optional target model path for reporting.
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
%         .contact_contract      generated-leg/contact block presence report.
%
%   See also: BUILD_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose');           opts.verbose           = true;  end
    if ~isfield(opts, 'smoke_time');        opts.smoke_time        = 0.005; end
    if ~isfield(opts, 'budget');            opts.budget            = 1000;  end
    if ~isfield(opts, 'report_path');       opts.report_path       = "";    end
    if ~isfield(opts, 'source_model_path'); opts.source_model_path = "";    end
    if ~isfield(opts, 'target_model_path'); opts.target_model_path = "";    end

    if ~bdIsLoaded(char(model_name))
        error('validate_3d_fullbody:notLoaded', ...
              'Model %s is not loaded.', model_name);
    end

    out = struct( ...
        'schema_version',       "3d_fullbody_validation_report.v1", ...
        'generated_at',         string(datetime('now')), ...
        'source_model_path',    string(opts.source_model_path), ...
        'target_model_path',    string(opts.target_model_path), ...
        'passed',              false, ...
        'total_blocks',        0, ...
        'nonvirtual_estimate', 0, ...
        'within_budget',       false, ...
        'logged_signals',      0, ...
        'smoke_sim_status',    "skipped", ...
        'smoke_sim_message',   "", ...
        'contact_contract',     struct(), ...
        'required_report_fields', [ ...
            "total_blocks"; ...
            "nonvirtual_estimate"; ...
            "logged_signals"; ...
            "smoke_sim_status"; ...
            "within_budget"; ...
            "contact_contract"], ...
        'artifact_policy',      "generated_only_ignored_by_git");

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

    % --- Check 2b: generated leg/contact contract --------------------
    out.contact_contract = local_contact_contract_report(char(model_name));
    if opts.verbose
        fprintf('  contact_contract     = %s\n', out.contact_contract.status);
        if ~out.contact_contract.passed
            fprintf('     missing: %s\n', strjoin(out.contact_contract.missing_blocks, ', '));
        end
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

    out.passed = out.within_budget && out.contact_contract.passed && ...
                 (out.smoke_sim_status == "success" || ...
                  out.smoke_sim_status == "skipped");
    if opts.verbose
        fprintf('  passed               = %s\n', ternary(out.passed, 'true', 'false'));
    end

    if strlength(string(opts.report_path)) > 0
        local_write_json(opts.report_path, out);
        if opts.verbose
            fprintf('  validation_report_path = %s\n', opts.report_path);
        end
    end
end


function out = ternary(cond, a, b)
    if cond; out = a; else; out = b; end
end


function local_write_json(path, payload)
    path = char(path);
    folder = fileparts(path);
    if strlength(string(folder)) > 0 && ~isfolder(folder)
        mkdir(folder);
    end
    fid = fopen(path, 'w');
    if fid < 0
        error('validate_3d_fullbody:reportOpenFailed', ...
              'Could not open validation report for writing: %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', jsonencode(payload, 'PrettyPrint', true));
    clear cleaner
end


function report = local_contact_contract_report(model_name)
    required = [ ...
        "Left Leg Kinetically Driven"; ...
        "Right Leg Kinetically Driven"; ...
        "Ground Contact Forces"; ...
        "LFoot_Ground_Contact_Force"; ...
        "RFoot_Ground_Contact_Force"; ...
        "Ground_Plane_Z0"; ...
        "LGroundReactionForce"; ...
        "RGroundReactionForce"];

    found = strings(0, 1);
    missing = strings(0, 1);
    for k = 1:numel(required)
        hits = find_system(model_name, ...
            'LookUnderMasks', 'all', ...
            'FollowLinks', 'on', ...
            'Name', char(required(k)));
        if isempty(hits)
            missing(end+1, 1) = required(k); %#ok<AGROW>
        else
            found(end+1, 1) = string(hits{1}); %#ok<AGROW>
        end
    end

    report = struct( ...
        'schema_version', "3d_fullbody_contact_contract.v1", ...
        'passed', isempty(missing), ...
        'status', ternary(isempty(missing), 'complete', 'missing_blocks'), ...
        'required_blocks', required, ...
        'found_blocks', found, ...
        'missing_blocks', missing, ...
        'static_pose_check', ...
            "block_presence_only_until contact force signals are routed");
end
