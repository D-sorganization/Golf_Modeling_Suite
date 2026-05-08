function test_3d_fullbody_loads()
%TEST_3D_FULLBODY_LOADS  Smoke test for the built model.
%
%   Skips cleanly if the built ``GolfSwing3D_FullBody.slx`` doesn't
%   exist yet (run ``build_3d_fullbody`` first).  Otherwise it loads
%   the model, runs a 5 ms simulation, and asserts:
%
%     * load succeeds
%     * sim completes without error
%     * validation report exposes the production gate fields
%     * nonvirtual block count <= 1000 (Home-license budget)
%     * signal allowlist is evaluated
%     * scaffold mode warns rather than fails when leg/contact blocks are
%       absent; production phases ratchet this in validate_3d_fullbody.
%
%   This is run by both MATLAB R2025b CI and any agent verifying the
%   build script.

    here = fileparts(mfilename('fullpath'));
    fullbody_root = fileparts(fileparts(here));
    target_slx = fullfile(fullbody_root, 'matlab', 'src', 'model', ...
                          'GolfSwing3D_FullBody.slx');

    if ~isfile(target_slx)
        warning('test_3d_fullbody_loads:notBuilt', ...
                ['GolfSwing3D_FullBody.slx not found at %s.  Run ' ...
                 '''build_3d_fullbody'' first to produce it.'], target_slx);
        return;
    end

    fprintf('Loading %s...\n', target_slx);
    [~, model_name, ~] = fileparts(target_slx);
    if bdIsLoaded(model_name); close_system(model_name, 0); end
    load_system(target_slx);
    cleanup = onCleanup(@() close_system(model_name, 0));

    fprintf('Validating...\n');
    out = validate_3d_fullbody(model_name, struct( ...
        'verbose',    true, ...
        'smoke_time', 0.005, ...
        'phase',      "scaffold", ...
        'budget',     1000, ...
        'warning_budget', 900, ...
        'target_model_path', target_slx));

    local_assert_validation_contract(out);
    assert(out.passed, 'Validation gate failed: %s', strjoin(out.failure_messages, '; '));
    assert(out.within_budget, ...
        'Block budget exceeded: %d / 1000 nonvirtual blocks', ...
        out.nonvirtual_estimate);
    assert(out.smoke_sim_status == "success" || ...
           out.smoke_sim_status == "warning", ...
        'Smoke sim failed: %s', out.smoke_sim_message);

    % --- Leg-chain presence (informational only — passes even when
    %     add_leg_chain is still in scaffold mode) -------------------
    has_leg_joints = local_has_leg_workspace_vars(model_name);
    if has_leg_joints
        fprintf('Leg-chain workspace variables: PRESENT\n');
    else
        fprintf('Leg-chain workspace variables: ABSENT (add_leg_chain in scaffold mode?)\n');
    end

    fprintf('test_3d_fullbody_loads: PASS\n');
end


function local_assert_validation_contract(out)
    required_fields = {'schema_version', 'phase', 'generated_model', ...
        'source_model_hash_sha256', 'total_block_count', ...
        'nonvirtual_block_estimate', 'nonvirtual_classification_method', ...
        'home_license_budget', 'warning_threshold', 'block_budget', ...
        'signal_count', 'required_signal_allowlist', 'leg_contact', ...
        'smoke_sim', 'failure_messages', 'warnings', 'passed'};
    for k = 1:numel(required_fields)
        assert(isfield(out, required_fields{k}), ...
            'Validation report missing required field: %s', required_fields{k});
    end
    assert(out.schema_version == "3d_fullbody_validation_report.v2", ...
        'Unexpected validation schema: %s', out.schema_version);
    assert(out.home_license_budget == 1000, 'Unexpected Home-license budget.');
    assert(out.warning_threshold == 900, 'Unexpected warning threshold.');
    assert(isfield(out.block_budget, 'status'), 'Block budget status missing.');
    assert(isfield(out.generated_model, 'exists'), 'Generated model presence missing.');
    assert(isfield(out.generated_model, 'timestamp'), 'Generated model timestamp missing.');
    assert(isfield(out.required_signal_allowlist, 'passed'), ...
        'Required signal allowlist result missing.');
    assert(isfield(out.leg_contact, 'phase_detected'), ...
        'Leg/contact phase detection missing.');
    assert(isfield(out.smoke_sim, 'duration_s'), 'Smoke sim duration missing.');
end


function tf = local_has_leg_workspace_vars(model_name)
    leg_keys = {'LHipStartPositionX', 'LKneeStartPosition', ...
                'LAnkleStartPositionX', 'RHipStartPositionX'};
    tf = false;
    try
        ws = get_param(model_name, 'ModelWorkspace');
        for k = 1:numel(leg_keys)
            if hasVariable(ws, leg_keys{k})
                tf = true;
                return;
            end
        end
    catch
        tf = false;
    end
end
