function out = add_leg_chain(model_name, opts)
%ADD_LEG_CHAIN  Add hip+knee+ankle+foot+contact subsystems to MODEL_NAME.
%
%   OUT = ADD_LEG_CHAIN(MODEL_NAME, OPTS) builds two leg subsystems
%   (Left Leg Kinetically Driven, Right Leg Kinetically Driven) that
%   mirror the existing arm subsystem conventions, plus a ground plane
%   and Sphere-Plane Spatial Contact Force per foot.
%
%   Per leg:
%     * Hip Gimbal Joint (3 DOF) — input parameters
%       L/RHipStartPosition{X,Y,Z} (deg), L/RHipStartVelocity{X,Y,Z},
%       and 7-coefficient polynomial torque per axis named
%       L/RHip{X,Y,Z}{A..G} so that
%       getPolynomialParameterInfo() picks them up automatically.
%     * Knee Revolute Joint (1 DOF) — L/RKneeStartPosition,
%       L/RKneeStartVelocity, L/RKnee{A..G}.
%     * Ankle Universal Joint (2 DOF) — L/RAnkleStartPosition{X,Y},
%       L/RAnkleStartVelocity{X,Y}, L/RAnkle{X,Y}{A..G}.
%     * Upper-Leg, Lower-Leg, Foot rigid bodies (Cylindrical /
%       Cylindrical / Brick) sized from new model-workspace variables
%       (UpperLegLength, LowerLegLength, FootLength, plus masses).
%     * Foot ↔ Ground Spatial Contact Force (Sphere/Plane).
%
%   The function MUTATES the loaded model in place; caller must
%   ``save_system`` afterward.
%
%   Args:
%       MODEL_NAME (char/string)  loaded Simulink model name.
%       OPTS (struct)
%         .verbose          default true.
%         .dry_run          default false; build the block list but
%                           don't actually call add_block.
%         .skip_contact     default false; build joints + bodies but
%                           don't add the contact-force network.
%         .leg_root_path    default ``<MODEL_NAME>``; you can sandbox
%                           the new chain into a wrapper subsystem by
%                           passing e.g. ``<MODEL_NAME>/LowerBody``.
%
%   Returns:
%       OUT (struct)
%         .blocks_added         total block count delta.
%         .blocks_per_phase     per-phase counts.
%         .new_workspace_vars   names of new model-workspace variables
%                               (lengths/masses/inertias).  Caller can
%                               attach defaults via setVariable when
%                               creating the SimulationInput.
%
%   STATUS (2026-05-07):
%   This function is currently a SCAFFOLD.  It declares the design
%   surface (block names, parameter names, port wiring) so the
%   getPolynomialParameterInfo + matcher pipelines pick up the new
%   joints automatically once the actual ``add_block`` calls are
%   uncommented.  Building the leg chain requires careful Simscape
%   Multibody library knowledge (which library pages each block lives
%   on, which mask parameters to set, which Frame ports to connect).
%
%   The intended usage flow:
%     1. Run ``build_3d_fullbody`` with ``opts.skip_legs=true`` first
%        to produce a clean copy with logging pruned.
%     2. Open the resulting ``GolfSwing3D_FullBody.slx`` in MATLAB.
%     3. Edit this function to fill in the actual ``add_block`` /
%        ``set_param`` / ``add_line`` calls below, OR build the leg
%        subsystems interactively in Simulink and update this script
%        to reproduce them.
%     4. Re-run ``build_3d_fullbody`` to validate.
%
%   Until then, calling this function with the default options reports
%   the design surface (returned struct) without modifying the model,
%   so the build script can complete and validate the pruned model.
%
%   See also: BUILD_3D_FULLBODY, PRUNE_REDUNDANT_LOGGING,
%             VALIDATE_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose');       opts.verbose       = true;  end
    if ~isfield(opts, 'dry_run');       opts.dry_run       = false; end
    if ~isfield(opts, 'skip_contact');  opts.skip_contact  = false; end
    if ~isfield(opts, 'leg_root_path');
        opts.leg_root_path = char(model_name);
    end

    if ~bdIsLoaded(char(model_name))
        error('add_leg_chain:notLoaded', ...
              'Model %s is not loaded.  Call load_system first.', model_name);
    end

    out = struct( ...
        'blocks_added',     0, ...
        'blocks_per_phase', struct( ...
            'workspace_vars',     0, ...
            'left_leg_subsystem', 0, ...
            'right_leg_subsystem',0, ...
            'ground_plane',       0, ...
            'contact_forces',     0), ...
        'new_workspace_vars', strings(0,1));

    if opts.verbose
        fprintf('add_leg_chain: SCAFFOLD MODE\n');
        fprintf('  declaring design surface; no add_block calls until you fill in body.\n');
    end

    % ---- Phase 1: declare new model-workspace variables -------------
    % Anthropometric defaults (de-Leva male, ~1.78m subject):
    %   UpperLegLength = 0.435 m   (greater trochanter to knee)
    %   LowerLegLength = 0.430 m   (knee to lateral malleolus)
    %   FootLength     = 0.260 m   (heel to toe)
    %   Plus masses + simple cylindrical-uniform inertias.
    new_vars = local_default_workspace_vars();
    if ~opts.dry_run
        try
            ws = get_param(char(model_name), 'ModelWorkspace');
            f = fieldnames(new_vars);
            for k = 1:numel(f)
                if ~hasVariable(ws, f{k})
                    assignin(ws, f{k}, new_vars.(f{k}));
                    out.new_workspace_vars(end+1, 1) = string(f{k});
                end
            end
        catch ME
            warning('add_leg_chain:wsAddFailed', ...
                    'Could not add workspace variables: %s', ME.message);
        end
    else
        out.new_workspace_vars = string(fieldnames(new_vars));
    end
    out.blocks_per_phase.workspace_vars = numel(out.new_workspace_vars);

    % ---- Phase 2-5 (TO BE FILLED IN) --------------------------------
    %
    % Below is the DESIGN SURFACE the build script will create when the
    % add_block / add_line calls are filled in.  Use this as a checklist
    % when implementing the actual block placement either by hand-tuned
    % add_block calls or by interactive Simulink build + diff.
    %
    %   Phase 2 — Left Leg Kinetically Driven (subsystem)
    %     Inports (from pelvis):  Pelvis_Frame
    %     Inports (from controller): JointTorqueLHip{X,Y,Z}, JointTorqueLKnee, JointTorqueLAnkle{X,Y}
    %     Outports: LFoot_Frame  (to contact force)
    %     Internal:
    %       Hip Gimbal Joint     (sm_lib/Joints/Gimbal Joint)
    %         Mask params: revolute primitives X / Y / Z, internal
    %         mechanics defined per "Kinetically_Driven_Gimbal_Joint.slx"
    %       Cylindrical Solid 'UpperLeg' (length=UpperLegLength)
    %       Knee Revolute Joint  (sm_lib/Joints/Revolute Joint)
    %       Cylindrical Solid 'LowerLeg' (length=LowerLegLength)
    %       Ankle Universal Joint (sm_lib/Joints/Universal Joint)
    %       Brick Solid 'Foot' (length=FootLength, width=FootWidth, height=FootHeight)
    %       Spherical Solid 'BallOfFoot_Sphere' (radius=0.03)
    %         — used by contact-force sphere; placed at toe end of foot
    %       Transform Sensors on each joint (logged)
    %       Inertia Sensors (cosmetic ones omitted to stay within budget)
    %
    %   Phase 3 — Right Leg Kinetically Driven (mirror of Phase 2 with
    %             segment lengths and start-positions mirrored about Y
    %             axis as appropriate)
    %
    %   Phase 4 — Ground plane (sm_lib/Body Elements/Infinite Plane,
    %             attached to World Frame at z=0)
    %
    %   Phase 5 — Contact forces (Spatial Contact Force per foot,
    %             sphere=foot.BallOfFoot_Sphere, plane=Ground.InfPlane,
    %             normal stiffness K=1e5 N/m, damping D=1000 N*s/m,
    %             static/kinetic friction 0.7/0.5).
    %
    % When you fill these phases in, increment
    % `out.blocks_per_phase.<phase>` so the validation script can
    % compute the post-build block count.

    out.blocks_added = sum(structfun(@double, out.blocks_per_phase));

    if opts.verbose
        fprintf('  declared design surface for legs + ground (no blocks added in scaffold mode)\n');
        fprintf('  new model-workspace variables (default values queued): %d\n', ...
            out.blocks_per_phase.workspace_vars);
    end
end


% =====================================================================
function vars = local_default_workspace_vars()
%LOCAL_DEFAULT_WORKSPACE_VARS  Anthropometric defaults for the leg chain.
%
%   Values from de Leva 1996 / Winter 2009 averaged for an adult male
%   golfer (~1.78 m, 80 kg), with cylindrical-uniform inertia
%   approximations.  Caller can override per-trial via setVariable on
%   the SimulationInput.
    vars = struct( ...
        ... % --- segment lengths (m) ---
        'UpperLegLength',           0.435, ...
        'LowerLegLength',           0.430, ...
        'FootLength',               0.260, ...
        'FootWidth',                0.095, ...
        'FootHeight',               0.060, ...
        'UpperLegRadius',           0.055, ...   % cylindrical thigh
        'LowerLegRadius',           0.040, ...   % cylindrical shin
        ... % --- masses (kg) — de Leva fractions of 80 kg total body ---
        'UpperLegMass',             0.10 * 80, ...
        'LowerLegMass',             0.0465 * 80, ...
        'FootMass',                 0.0145 * 80, ...
        ... % --- contact parameters ---
        'GroundContactStiffness',   1e5, ...
        'GroundContactDamping',     1000, ...
        'GroundFrictionStatic',     0.7, ...
        'GroundFrictionKinetic',    0.5, ...
        ... % --- joint start positions (degrees) — neutral standing ---
        'LHipStartPositionX',       0.0, ...
        'LHipStartPositionY',       0.0, ...
        'LHipStartPositionZ',       0.0, ...
        'RHipStartPositionX',       0.0, ...
        'RHipStartPositionY',       0.0, ...
        'RHipStartPositionZ',       0.0, ...
        'LKneeStartPosition',       0.0, ...
        'RKneeStartPosition',       0.0, ...
        'LAnkleStartPositionX',     0.0, ...
        'LAnkleStartPositionY',     0.0, ...
        'RAnkleStartPositionX',     0.0, ...
        'RAnkleStartPositionY',     0.0);
end
